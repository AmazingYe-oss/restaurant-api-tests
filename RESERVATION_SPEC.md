# 预约业务需求与接口约定（测试工作稿）

版本：2026-11-03。范围：当前预约模块。依据：SUT e0ebb51b3c53118bf73e4cd044372edc5eb01c95 的 Controller、请求/响应DTO、Validator、TimeUtil、状态及权限服务，结合已有真实运行记录。

**性质：从当前实现整理的测试约定，不是原作者签署的需求文档。** 明确的规则用于形成预期；疑问、文档冲突和实现缺陷单独记录，不以实际错误响应反向修改预期。本稿只覆盖预约模块，其他模块在设计前补齐相应约定。

## 一、业务规则

1. 普通客户仅能操作自己的预约；管理员有相应授权例外。
2. 请求提供真实存在的餐厅、桌位、客户；桌位需属于指定餐厅。
3. 人数为整数，DTO允许1–50，且不能超过具体桌位容量。本机桌位1容量4。
4. 预约不能在过去。日期和当天时刻判断依赖服务端日期/时区；目前容器UTC、本机Asia/Shanghai，业务时区尚待确认。
5. 固定时长120分钟；预约开始到结束的整个时段应在营业时间内。本机餐厅1营业09:00–22:00，因此同日有效开始范围09:00–20:00，包含端点；秒级/跨天场景另行设计，不据分钟样例宣布全覆盖。
6. PENDING/CONFIRMED为冲突检查的活跃预约，代码还包含15分钟缓冲；同桌位重叠预约应拒绝。并发重复预约BUG-001已复现，未修复，暂停深入。
7. 相同幂等键和相同内容重试返回已有预约；同键不同内容拒绝。当前业务比较字段见ReservationService，不能仅由返回同id证明数据库没有其他记录。
8. 创建初始PENDING；取消改为CANCELLED，不物理删除，仍可查询。

## 二、创建预约

POST /api/reservations

请求头：Authorization: Bearer <有效Token>；Idempotency-Key 为8–64位字母/数字/点/下划线/连字符。Controller虽声明后者可选，但业务层要求提供，记录为契约不一致点。独立新请求用新键，同次重试复用键。

请求JSON：

| 字段 | 类型 | 要求 |
| --- | --- | --- |
| restaurantId | 整数 | 必填，存在的餐厅编号 |
| customerId | 整数 | 必填，授权操作的客户编号 |
| tableId | 整数 | 必填，属于该餐厅的桌位编号，不是预约编号 |
| reservationDate | 日期字符串 | 必填，YYYY-MM-DD，非过去日期 |
| reservationTime | 时间字符串 | 必填；测试统一使用HH:mm:ss，合法时间且满足营业规则 |
| numberOfGuests | 整数 | 必填，1–50且不超过桌位容量 |

成功HTTP 201，返回ReservationResponse；幂等重放当前同样201。

| 成功字段 | 类型/含义 |
| --- | --- |
| id | 整数，预约编号 |
| customerId / restaurantId / tableId | 整数，关联编号 |
| reservationDate | 日期字符串 |
| reservationTime | 开始时间字符串 |
| reservationEndTime | 结束时间字符串 |
| numberOfGuests | 整数 |
| status | 状态字符串，创建时PENDING |
| createdAt / updatedAt | 时间字符串，具体值动态生成 |

**成功响应没有约定path/message字段；错误响应也没有约定reservationTime等业务字段。**

常见失败：HTTP400参数或业务校验失败，401未认证，403无权限，404关联资源不存在，409预约冲突或幂等键不一致。错误优先级随校验顺序可能不同，应让非目标前提都合法。非法日期/时间格式此前触发500，是已观察异常处理问题，不能把它写成理想成功验收标准。

## 三、查询和取消

GET /api/reservations/{id}：本人或有权限管理员查询；成功200及同类预约JSON。取消后查询仍200及CANCELLED。

DELETE /api/reservations/{id}：取消预约，成功204，无响应体；不能调用response.json()。客户B取消客户A预约应403且预约不应变更。Swagger曾列200但实际204，属于文档不一致观察。

## 四、错误响应结构

由ErrorResponse及异常处理生成：

| 字段 | 含义 |
| --- | --- |
| timestamp | 动态发生时间 |
| status | 数字错误状态码 |
| error | 错误类别描述 |
| message | 错误原因 |
| path | 请求路径 |

错误响应结构示意（非实际抓包，动态字段省略）：

```json
{
  "status": 400,
  "error": "Validation Failed",
  "message": "Reservation time is outside restaurant hours",
  "path": "/api/reservations"
}
```

常用message（业务校验；必填校验可能带Validation failed前缀）：
- 开始时刻在营业时间外：Reservation time is outside restaurant hours。
- 完整时段超过营业时间：Reservation time slot is not within restaurant hours。
- 超过桌位容量：Number of guests exceeds table capacity。
- 重复预约：Table is already booked for this time。
- 同键不同参数：Idempotency-Key was already used for a different reservation request。

## 五、本次营业时间用例验收

未来日期、合法身份、人数2、桌位无有效冲突，六组顺序执行并清理：08:59拒绝400；09:00/09:01/19:59/20:00允许201；20:01拒绝400。这组用例覆盖有效时间范围两端的分钟级边界。

所有场景先比较HTTP与预期；成功分支才读预约字段并检查时间/PENDING；失败分支检查错误status/path/message，不读取reservationTime。用例成功/失败不共用一种响应结构。

执行结果为 6 条通过。成功响应检查预约时间和状态，错误响应检查错误状态与请求路径。

## 六、尚待确认

业务时区、跨天营业、时间精度、异常响应文案稳定性及部分权限/状态组合未获得作者需求确认。不得为保证通过而将未知行为写成需求。后续新场景开始前先补相应规则、输入输出和来源。

## 状态迁移实现约定（2026-11-03补充）
依据ReservationStatusManager：PENDING仅可到CONFIRMED/CANCELLED；CONFIRMED仅可到COMPLETED/CANCELLED；CANCELLED/COMPLETED不可再迁移，包括重复设置同状态。禁止迁移抛ValidationException，按当前异常映射预期400/Invalid status transition。PUT /api/reservations/{id}/status需要管理员权限，普通客户可用本人DELETE取消；不能拿403作为非法状态迁移验证成功。重复取消是否应幂等是业务需求待确认点，目前仅记录实现规则。
