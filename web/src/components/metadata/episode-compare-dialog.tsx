/**
 * 分集来源对比: 对照各站 raw 与库内合并结果; 可选用某一来源整表覆盖写入.
 */
import {
  Badge,
  Button,
  Group,
  Modal,
  Radio,
  ScrollArea,
  Stack,
  Table,
  Text,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  applyEpisodesFromSourceMutation,
  getMetadataQueryKey,
} from "@/client/@tanstack/react-query.gen";
import type { EpisodeResponse, MetadataResponse } from "@/client/types.gen";
import { extractErrorMessage } from "@/lib/api-error";
import { isRecord } from "@/lib/utils";

type EpisodeCell = {
  season: number;
  episode: number;
  title: string | null;
  plot: string | null;
};

type SourceColumn = {
  key: string;
  label: string;
  episodeCount: number | null;
  byKey: Map<string, EpisodeCell>;
  selectable: boolean;
};

function epKey(season: number, episode: number): string {
  return `${season}:${episode}`;
}

function asPositiveInt(value: unknown): number | null {
  if (typeof value === "number" && Number.isInteger(value) && value >= 1) return value;
  if (typeof value === "string" && /^\d+$/.test(value.trim())) {
    const n = Number(value.trim());
    return n >= 1 ? n : null;
  }
  return null;
}

function parseEpisodeCell(raw: unknown): EpisodeCell | null {
  if (!isRecord(raw)) return null;
  const episode = asPositiveInt(raw.episode);
  if (episode == null) return null;
  const season = asPositiveInt(raw.season) ?? 1;
  const title =
    typeof raw.title === "string" && raw.title.trim().length > 0 ? raw.title.trim() : null;
  const plot = typeof raw.plot === "string" && raw.plot.trim().length > 0 ? raw.plot.trim() : null;
  return { season, episode, title, plot };
}

function buildSourceColumns(raw: MetadataResponse["raw"]): SourceColumn[] {
  const out: SourceColumn[] = [];
  if (!isRecord(raw)) return out;
  for (const [site, payload] of Object.entries(raw)) {
    if (!isRecord(payload)) continue;
    const byKey = new Map<string, EpisodeCell>();
    const list = payload.episodes;
    if (Array.isArray(list)) {
      for (const item of list) {
        const cell = parseEpisodeCell(item);
        if (cell == null) continue;
        byKey.set(epKey(cell.season, cell.episode), cell);
      }
    }
    const episodeCount = asPositiveInt(payload.episode_count);
    if (byKey.size === 0 && episodeCount == null) continue;
    out.push({ key: site, label: site, episodeCount, byKey, selectable: true });
  }
  return out.sort((a, b) => a.label.localeCompare(b.label));
}

function buildDbColumn(episodes: EpisodeResponse[]): SourceColumn {
  const byKey = new Map<string, EpisodeCell>();
  let maxEp = 0;
  for (const ep of episodes) {
    byKey.set(epKey(ep.season, ep.episode), {
      season: ep.season,
      episode: ep.episode,
      title: ep.title ?? null,
      plot: ep.plot ?? null,
    });
    if (ep.season === 1) maxEp = Math.max(maxEp, ep.episode);
  }
  return {
    key: "__db__",
    label: "DB",
    episodeCount: maxEp > 0 ? maxEp : null,
    byKey,
    selectable: false,
  };
}

function collectRowKeys(columns: SourceColumn[]): Array<{ season: number; episode: number }> {
  const seen = new Set<string>();
  const rows: Array<{ season: number; episode: number }> = [];
  for (const col of columns) {
    for (const cell of col.byKey.values()) {
      const k = epKey(cell.season, cell.episode);
      if (seen.has(k)) continue;
      seen.add(k);
      rows.push({ season: cell.season, episode: cell.episode });
    }
    if (col.episodeCount != null) {
      for (let n = 1; n <= col.episodeCount; n++) {
        const k = epKey(1, n);
        if (seen.has(k)) continue;
        seen.add(k);
        rows.push({ season: 1, episode: n });
      }
    }
  }
  return rows.sort((a, b) => a.season - b.season || a.episode - b.episode);
}

function cellLabel(
  cell: EpisodeCell | undefined,
  episode: number,
  untitled: (n: number) => string,
): string {
  if (cell == null) return "—";
  if ((cell.title || "").trim()) return cell.title!.trim();
  return untitled(episode);
}

export type EpisodeCompareDialogProps = {
  metadata: MetadataResponse;
  episodes: EpisodeResponse[];
  opened: boolean;
  onClose: () => void;
  onApplied?: () => void;
};

export function EpisodeCompareDialog({
  metadata,
  episodes,
  opened,
  onClose,
  onApplied,
}: EpisodeCompareDialogProps) {
  const { t } = useTranslation(["metadata", "common"]);
  const queryClient = useQueryClient();
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  const { columns, rows, hasAny, selectableSources } = useMemo(() => {
    const sources = buildSourceColumns(metadata.raw);
    const db = buildDbColumn(episodes);
    const cols = [...sources, db];
    return {
      columns: cols,
      rows: collectRowKeys(cols),
      hasAny: sources.length > 0 || episodes.length > 0,
      selectableSources: sources,
    };
  }, [metadata.raw, episodes]);

  const applyMutation = useMutation({
    ...applyEpisodesFromSourceMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getMetadataQueryKey({ path: { metadata_id: metadata.id } }),
      });
      notifications.show({
        message: t("episodeCompare.applied"),
        color: "teal",
      });
      setSelectedSource(null);
      onApplied?.();
    },
    onError: (err) => {
      notifications.show({
        message: extractErrorMessage(err, t("common:toast.operationFailed")),
        color: "red",
      });
    },
  });

  const canApply =
    selectedSource != null &&
    selectableSources.some((s) => s.key === selectedSource) &&
    !applyMutation.isPending;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`${t("episodeCompare.title")} — ${metadata.number}`}
      size="90%"
      styles={{ body: { maxHeight: "75vh", display: "flex", flexDirection: "column" } }}
    >
      {!hasAny ? (
        <Text c="dimmed" size="sm" py="xl" ta="center">
          {t("episodeCompare.empty")}
        </Text>
      ) : (
        <Stack gap="md" style={{ flex: 1, minHeight: 0 }}>
          <Text size="xs" c="dimmed">
            {t("episodeCompare.hint")}
          </Text>
          <Radio.Group
            value={selectedSource ?? ""}
            onChange={(v) => setSelectedSource(v || null)}
            label={t("episodeCompare.pickSource")}
          >
            <Group gap="sm" mt={6} wrap="wrap">
              {selectableSources.map((col) => (
                <Radio
                  key={col.key}
                  value={col.key}
                  label={
                    col.episodeCount != null
                      ? `${col.label} (${t("detail.episodeCount", { count: col.episodeCount })})`
                      : col.label
                  }
                />
              ))}
            </Group>
          </Radio.Group>
          <ScrollArea style={{ flex: 1, minHeight: 0 }} type="auto">
            <Table striped highlightOnHover withTableBorder withColumnBorders stickyHeader>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th style={{ whiteSpace: "nowrap" }}>
                    {t("episodeCompare.episodeCol")}
                  </Table.Th>
                  {columns.map((col) => (
                    <Table.Th
                      key={col.key}
                      style={{
                        minWidth: 140,
                        background:
                          selectedSource === col.key
                            ? "var(--mantine-color-indigo-light)"
                            : undefined,
                      }}
                    >
                      <Group gap={6} wrap="nowrap">
                        <Text size="sm" fw={500}>
                          {col.key === "__db__" ? t("episodeCompare.merged") : col.label}
                        </Text>
                        {selectedSource === col.key ? (
                          <Badge size="xs" color="indigo">
                            {t("episodeCompare.selected")}
                          </Badge>
                        ) : null}
                      </Group>
                    </Table.Th>
                  ))}
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rows.map((row) => {
                  const k = epKey(row.season, row.episode);
                  const epLabel =
                    row.season > 1 ? `S${row.season}E${row.episode}` : `E${row.episode}`;
                  return (
                    <Table.Tr key={k}>
                      <Table.Td>
                        <Text size="sm" ff="monospace">
                          {epLabel}
                        </Text>
                      </Table.Td>
                      {columns.map((col) => {
                        const cell = col.byKey.get(k);
                        const title = cellLabel(cell, row.episode, (n) =>
                          t("detail.episodeUntitled", { n }),
                        );
                        const hasTitle = Boolean((cell?.title || "").trim());
                        const onlyCount =
                          cell == null &&
                          col.episodeCount != null &&
                          row.season === 1 &&
                          row.episode <= col.episodeCount;
                        return (
                          <Table.Td
                            key={col.key}
                            style={{
                              background:
                                selectedSource === col.key
                                  ? "var(--mantine-color-indigo-light)"
                                  : undefined,
                            }}
                          >
                            <Stack gap={2}>
                              <Text
                                size="sm"
                                c={cell == null && !onlyCount ? "dimmed" : undefined}
                                lineClamp={2}
                              >
                                {onlyCount && cell == null
                                  ? t("episodeCompare.countOnly")
                                  : title}
                              </Text>
                              {hasTitle ? null : cell != null ? (
                                <Text size="xs" c="dimmed">
                                  {t("episodeCompare.noTitle")}
                                </Text>
                              ) : null}
                              {cell?.plot ? (
                                <Text size="xs" c="dimmed" lineClamp={2}>
                                  {cell.plot}
                                </Text>
                              ) : null}
                            </Stack>
                          </Table.Td>
                        );
                      })}
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>
          </ScrollArea>
          <Group justify="flex-end" gap="sm">
            <Button variant="default" onClick={onClose}>
              {t("common:actions.cancel")}
            </Button>
            <Button
              disabled={!canApply}
              loading={applyMutation.isPending}
              onClick={() => {
                if (selectedSource == null || metadata.id == null) return;
                applyMutation.mutate({
                  path: { metadata_id: metadata.id },
                  body: { source: selectedSource },
                });
              }}
            >
              {t("episodeCompare.apply")}
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
