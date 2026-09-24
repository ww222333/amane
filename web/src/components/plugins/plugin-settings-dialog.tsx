import { Button, Group, Modal, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useTranslation } from "react-i18next";
import type { PluginResponse } from "@/client/types.gen";
import type { JSONSchemaObject } from "@/components/schema-form/schema";
import { SchemaForm } from "@/components/schema-form/schema-form";
import { useTestPlugin } from "@/hooks/use-plugins";

interface PluginSettingsDialogProps {
  plugin: PluginResponse;
  schema: JSONSchemaObject;
  opened: boolean;
  onClose: () => void;
  onSave: (config: Record<string, unknown>) => void;
  saving: boolean;
}

/**
 * 插件配置渲染在悬浮框中, 不占用插件列表的面积.
 *
 * 保存条经 `UnsavedChangesBar` 的 affix 定位固定在视口底 (z-index 高于 Modal), 因此 body
 * 要预留底部空间; 该定位依赖 Modal 打开态的 transform 作为包含块, 不允许把保存条放回表单流.
 *
 * 「测试」使用已保存配置; 修改 Cookie 等后须先保存再测.
 */
export function PluginSettingsDialog({
  plugin,
  schema,
  opened,
  onClose,
  onSave,
  saving,
}: PluginSettingsDialogProps) {
  const { t } = useTranslation(["plugins", "settings", "common"]);
  const testMutation = useTestPlugin();
  const supportsTest = plugin.supports_test === true;

  const handleTest = () => {
    testMutation.mutate(
      {
        path: { plugin_id: plugin.descriptor.id },
        body: { config: {} },
      },
      {
        onSuccess: (result) => {
          notifications.show({
            color: result.ok ? "green" : "red",
            message: result.detail || (result.ok ? t("testOk") : t("testFailed")),
          });
        },
      },
    );
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={t("settingsTitle", { name: plugin.descriptor.name })}
      size="48rem"
      centered
      styles={{ body: { paddingBottom: 88 } }}
    >
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start" wrap="nowrap" gap="sm">
          <Text size="xs" c="dimmed" ff="monospace">
            {plugin.descriptor.id}
          </Text>
          {supportsTest ? (
            <Button
              size="xs"
              variant="light"
              onClick={handleTest}
              loading={testMutation.isPending}
              disabled={saving}
            >
              {t("test")}
            </Button>
          ) : null}
        </Group>
        {supportsTest ? (
          <Text size="xs" c="dimmed">
            {t("testHint")}
          </Text>
        ) : null}
        <SchemaForm
          schema={schema}
          prefix="pluginConfig"
          // 配置直接取列表数据: 保存会失效并重新取回列表, 再次打开弹窗必须看到新值.
          values={plugin.config.config ?? {}}
          i18nPrefix="settings:fields"
          actionsPlacement="affix"
          submitLabel={t("save")}
          onSave={onSave}
          saving={saving}
        />
      </Stack>
    </Modal>
  );
}
