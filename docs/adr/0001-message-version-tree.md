---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'c4ff84f5-0c1d-4b5a-b6c1-f1f1cb4dc928'
  PropagateID: 'c4ff84f5-0c1d-4b5a-b6c1-f1f1cb4dc928'
  ReservedCode1: '54a747a5-2ef7-420c-af2e-0c981ed901e8'
  ReservedCode2: '54a747a5-2ef7-420c-af2e-0c981ed901e8'
---

# ADR-0001: 消息版本树而非覆盖更新

用户编辑消息后重发、或重新生成 AI 回复时，旧消息不删除/不覆盖，而是新消息通过 `parent_message_id` 指向旧消息，形成版本树。

这是因为覆盖会丢失对话历史，无法追溯"用户改了什么""AI 之前怎么回答的"。版本树的代价是查询当前对话链时需要从最新节点回溯而非直接读取——但对话场景下几乎不需要查看历史版本，用 `parent_message_id IS NULL` 查最新版本即可，额外成本可忽略。