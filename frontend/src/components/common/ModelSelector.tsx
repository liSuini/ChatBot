import { Select } from 'antd'
import { useEffect } from 'react'
import { useSettingsStore } from '../../stores/settingsStore'

export default function ModelSelector() {
  const provider = useSettingsStore((s) => s.provider)
  const providers = useSettingsStore((s) => s.providers)
  const setProvider = useSettingsStore((s) => s.setProvider)
  const loadProviders = useSettingsStore((s) => s.loadProviders)

  useEffect(() => {
    loadProviders()
  }, [loadProviders])

  return (
    <Select
      value={provider}
      onChange={setProvider}
      style={{ width: '100%' }}
      placeholder="选择模型"
      options={providers.map((p) => ({ value: p.name, label: p.display_name }))}
    />
  )
}
