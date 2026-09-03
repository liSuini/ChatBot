---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '486957c6-fc65-49ca-b599-8434512badb6'
  PropagateID: '486957c6-fc65-49ca-b599-8434512badb6'
  ReservedCode1: 'c6291c94-ffe1-4708-9cf0-e4982970435a'
  ReservedCode2: 'c6291c94-ffe1-4708-9cf0-e4982970435a'
---

# ADR-0002: 聚合根间不持有对象引用，仅持 ID

User 聚合不直接持有 Conversation 列表，Conversation 不持有 User 对象；Document 与 Conversation 之间也没有直接引用。跨聚合关联只用 ID。

这是刻意选择而非 ORM 懒加载。原因：团队内部工具的数据量级下，按 ID 查询性能足够；不持有对象引用使得各聚合可独立加载、独立测试、未来若拆分微服务只需把 ID 查询换成 HTTP 调用，聚合内部代码零改动。代价是业务层需要显式组装多个聚合的数据（如展示会话列表需要关联用户信息时需多次查询），但对于本项目的查询模式这个代价可接受。