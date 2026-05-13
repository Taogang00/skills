# 异常处理与日志规范

## 1. 异常处理规范

### 异常处理规则

| 规则ID | 级别 | 规则 |
|---|---|---|
| E-001 | 【强制】 | 不要捕获 `Exception`、`Throwable` 作为通用兜底，要精确捕获异常 |
| E-002 | 【强制】 | 捕获异常后，如果不处理，则将异常抛出，不允许只打 `e.printStackTrace()` |
| E-003 | 【强制】 | 有 `try` 块放到了事务代码中，`catch` 异常后，如果需要回滚事务，一定要注意手动回滚事务 |
| E-004 | 【强制】 | `finally` 块必须对资源对象、流对象进行关闭，推荐使用 `try-with-resources` |
| E-005 | 【强制】 | 不要在 `finally` 块中使用 `return`，会吞掉前面的异常 |
| E-006 | 【强制】 | 自定义异常须携带原始异常信息（cause），不要丢失堆栈 |
| E-007 | 【推荐】 | 方法签名中，不建议使用 `throws Exception`，应声明具体的受检异常 |

## 2. 日志规范

### 基本规则

```java
// 【强制】使用 Slf4j + @Slf4j注解（Lombok），禁止使用System.out.println
@Slf4j
@Service
public class OrderServiceImpl implements OrderService {

    public void processOrder(Long orderId) {
        // 【强制】使用占位符，禁止字符串拼接（字符串拼接在不打印时也会计算）
        log.info("开始处理订单, orderId:{}", orderId);

        // ❌ 错误：字符串拼接
        log.info("开始处理订单, orderId:" + orderId);

        // 【推荐】条件判断（debug日志需要）
        if (log.isDebugEnabled()) {
            log.debug("订单详情: {}", JSON.toJSONString(order));
        }
    }
}
```

### 日志级别使用场景

| 级别 | 使用场景 |
|---|---|
| `ERROR` | 影响系统功能的严重错误，需要立即告警处理（如数据库连接失败、第三方调用失败且不可恢复） |
| `WARN` | 潜在问题，不影响当前操作但需要关注（如参数校验失败、业务规则不满足、性能警告） |
| `INFO` | 核心业务流程节点，便于追踪请求链路（接口入参、关键业务步骤、接口出参） |
| `DEBUG` | 开发调试信息，生产环境关闭（详细的中间状态、SQL参数等） |

```java
@Override
public OrderVO createOrder(CreateOrderRequest request) {
    // INFO：记录核心业务操作（入参用JSON序列化，便于排查）
    log.info("创建订单, userId:{}, 商品数量:{}", request.getUserId(), request.getItems().size());

    try {
        // 业务处理...
        OrderPO order = buildOrder(request);
        orderMapper.insert(order);

        // INFO：记录关键结果
        log.info("订单创建成功, orderId:{}, userId:{}", order.getId(), request.getUserId());
        return orderConverter.toVO(order);

    } catch (StockInsufficientException e) {
        // WARN：业务预期内的异常（库存不足属于正常业务场景）
        log.warn("创建订单失败，库存不足, userId:{}, skuId:{}", request.getUserId(), e.getSkuId());
        throw e;
    } catch (Exception e) {
        // ERROR：非预期的系统异常
        log.error("创建订单系统异常, userId:{}, request:{}", request.getUserId(),
                JSON.toJSONString(request), e);  // 最后一个参数是Throwable，自动打印堆栈
        throw new BusinessException(ErrorCode.SYSTEM_ERROR, e);
    }
}
```

### 日志配置规范（logback-spring.xml 要点）

```xml
<!-- 生产环境日志配置要点 -->
<!-- 1. 按天滚动，保留30天 -->
<!-- 2. 单文件最大500MB -->
<!-- 3. ERROR 单独输出到 error.log -->
<!-- 4. 包含：时间、级别、线程、TraceId、类名、行号、消息 -->

<!-- 推荐日志格式 -->
<!-- %d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{50}:%line - %msg%n -->
```
