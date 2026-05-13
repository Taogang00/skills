# 代码优化与性能调优指导

## 1. 代码优化审查清单

拿到代码后，按以下优先级检查：

### P0 - 必须修复（影响功能/安全/数据正确性）

- [ ] **SQL注入**：是否有字符串拼接SQL，应使用预处理语句/MyBatis #{} 参数绑定
- [ ] **空指针异常**：链式调用未判null，可能NPE的场景
- [ ] **资源泄漏**：连接、流、Session等未关闭
- [ ] **事务失效**：`@Transactional` 加在非public方法、同类内部调用、异常被catch吞掉
- [ ] **线程安全**：多线程环境下的共享变量未同步
- [ ] **敏感信息泄露**：密码、Token等出现在日志或响应体中

### P1 - 建议修复（影响性能/可维护性）

- [ ] **N+1查询**：循环内部进行DB查询，应改为批量查询
- [ ] **大事务**：事务包含了不必要的查询操作，应缩小事务范围
- [ ] **缺少索引**：频繁查询的字段无索引
- [ ] **魔法值**：直接使用数字/字符串字面量，应定义为常量/枚举
- [ ] **方法过长**：单方法超过80行，应拆分为多个私有方法
- [ ] **深层嵌套**：if/for 嵌套超过3层，考虑提前return或重构

### P2 - 可以优化（代码质量/规范）

- [ ] **命名不规范**：不符合阿里规范的命名
- [ ] **缺少注释**：公共方法、复杂逻辑缺少注释
- [ ] **日志不规范**：使用字符串拼接，日志级别不合适
- [ ] **返回null集合**：集合类型应返回空集合

## 2. 常见性能问题与优化方案

### 2.1 数据库优化

```java
// ❌ N+1查询问题
List<OrderPO> orders = orderMapper.selectByUserId(userId);
for (OrderPO order : orders) {
    // 每次循环都查一次DB！100个订单 = 101次查询
    List<OrderItemPO> items = orderItemMapper.selectByOrderId(order.getId());
    order.setItems(items);
}

// ✅ 批量查询
List<OrderPO> orders = orderMapper.selectByUserId(userId);
if (!orders.isEmpty()) {
    List<Long> orderIds = orders.stream().map(OrderPO::getId).collect(Collectors.toList());
    List<OrderItemPO> allItems = orderItemMapper.selectByOrderIds(orderIds);
    // 按orderId分组
    Map<Long, List<OrderItemPO>> itemsMap = allItems.stream()
            .collect(Collectors.groupingBy(OrderItemPO::getOrderId));
    orders.forEach(order -> order.setItems(itemsMap.getOrDefault(order.getId(), List.of())));
}

// ✅ 分页查询（禁止全量加载后内存分页）
// ❌ 错误
List<OrderPO> allOrders = orderMapper.selectAll();  // OOM风险
List<OrderPO> page = allOrders.subList(0, 20);

// ✅ 正确
Page<OrderPO> page = orderMapper.selectPage(new Page<>(pageNum, pageSize), queryWrapper);
```

### 2.2 缓存使用规范

```java
@Service
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    private static final String USER_CACHE_KEY = "user:info:";
    private static final Duration CACHE_TTL = Duration.ofMinutes(30);

    @Override
    public UserVO getUserById(Long userId) {
        String cacheKey = USER_CACHE_KEY + userId;

        // 1. 查缓存
        Object cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return (UserVO) cached;
        }

        // 2. 缓存未命中，查DB
        UserPO userPO = userMapper.selectById(userId);
        if (userPO == null) {
            // 缓存空值，防止缓存穿透（设置较短TTL）
            redisTemplate.opsForValue().set(cacheKey, "", Duration.ofSeconds(30));
            throw new ResourceNotFoundException("用户不存在");
        }

        UserVO userVO = userConverter.toVO(userPO);
        // 3. 写缓存（加随机偏移防止缓存雪崩）
        Duration ttl = CACHE_TTL.plusSeconds(new Random().nextInt(60));
        redisTemplate.opsForValue().set(cacheKey, userVO, ttl);

        return userVO;
    }

    @Override
    public void updateUser(Long userId, UpdateUserRequest request) {
        // 更新DB
        userMapper.updateById(buildUpdatePO(userId, request));
        // 删除缓存（Cache Aside Pattern）
        redisTemplate.delete(USER_CACHE_KEY + userId);
    }
}
```

### 2.3 大事务优化

```java
// ❌ 大事务：包含了不必要的查询，锁持有时间长
@Transactional(rollbackFor = Exception.class)
public void createOrder(CreateOrderRequest request) {
    // 查询（不需要事务）
    ProductPO product = productMapper.selectById(request.getProductId());
    UserPO user = userMapper.selectById(request.getUserId());

    // 发送HTTP请求（不应该在事务中！）
    CouponVO coupon = couponService.validateCoupon(request.getCouponId());

    // 真正需要事务的写操作
    orderMapper.insert(buildOrder(request, product, user));
    inventoryMapper.deduct(request.getProductId(), request.getQuantity());
}

// ✅ 缩小事务范围
public void createOrder(CreateOrderRequest request) {
    // 事务外：查询操作
    ProductPO product = productMapper.selectById(request.getProductId());
    UserPO user = userMapper.selectById(request.getUserId());
    CouponVO coupon = couponService.validateCoupon(request.getCouponId());

    // 事务内：只包含写操作
    doCreateOrderInTransaction(request, product, user, coupon);
}

@Transactional(rollbackFor = Exception.class)
public void doCreateOrderInTransaction(CreateOrderRequest request, ProductPO product,
                                        UserPO user, CouponVO coupon) {
    orderMapper.insert(buildOrder(request, product, user));
    inventoryMapper.deduct(request.getProductId(), request.getQuantity());
}
```

### 2.4 对象转换优化（MapStruct）

```java
// ✅ 使用 MapStruct 替代手动 set（零反射，编译期生成，性能最优）
@Mapper(componentModel = "spring")
public interface UserConverter {

    @Mapping(source = "userName", target = "name")
    @Mapping(target = "password", ignore = true)  // 忽略敏感字段
    UserVO toVO(UserPO userPO);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createTime", expression = "java(java.time.LocalDateTime.now())")
    UserPO toPO(CreateUserRequest request);

    List<UserVO> toVOList(List<UserPO> userPOList);
}
```

## 3. JVM 与内存优化建议

```java
// 避免在循环中创建对象
// ❌ 每次循环创建 SimpleDateFormat
for (String dateStr : dateStrList) {
    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");  // 每次new
    Date date = sdf.parse(dateStr);
}

// ✅ 使用线程安全的 DateTimeFormatter（JDK8+）
private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

for (String dateStr : dateStrList) {
    LocalDate date = LocalDate.parse(dateStr, DATE_FORMATTER);  // 线程安全，可复用
}

// 大集合及时释放引用
public void processLargeData() {
    List<String> largeList = loadLargeData();
    process(largeList);
    largeList = null;  // 帮助GC回收（方法结束后也会自动回收，但提前null有助于长方法）
}
```

## 4. Spring Boot 性能配置

```yaml
# application.yml 性能相关配置
spring:
  datasource:
    hikari:
      # 连接池配置
      minimum-idle: 10
      maximum-pool-size: 20
      idle-timeout: 600000    # 空闲连接超时（10分钟）
      connection-timeout: 30000
      max-lifetime: 1800000   # 连接最大存活时间（30分钟）

  redis:
    lettuce:
      pool:
        min-idle: 5
        max-idle: 10
        max-active: 20

  mvc:
    async:
      request-timeout: 30000  # 异步请求超时

server:
  tomcat:
    threads:
      min-spare: 10
      max: 200
    accept-count: 100
    connection-timeout: 20000
```

## 5. 代码重构模式

### 卫语句（Guard Clause）替代深层嵌套

```java
// ❌ 嵌套地狱
public String processOrder(OrderPO order) {
    if (order != null) {
        if (order.getStatus() == 1) {
            if (order.getAmount() > 0) {
                if (order.getUserId() != null) {
                    return "处理成功";
                } else {
                    return "用户ID为空";
                }
            } else {
                return "金额无效";
            }
        } else {
            return "状态不允许";
        }
    } else {
        return "订单不存在";
    }
}

// ✅ 卫语句（提前return）
public String processOrder(OrderPO order) {
    if (order == null) return "订单不存在";
    if (order.getStatus() != 1) return "状态不允许";
    if (order.getAmount() <= 0) return "金额无效";
    if (order.getUserId() == null) return "用户ID为空";

    return "处理成功";
}
```

### 策略模式替代大量 if-else

```java
// ❌ 大量 if-else（每次新增业务都要改这个方法）
public BigDecimal calculateDiscount(String userType, BigDecimal price) {
    if ("VIP".equals(userType)) {
        return price.multiply(new BigDecimal("0.8"));
    } else if ("SVIP".equals(userType)) {
        return price.multiply(new BigDecimal("0.7"));
    } else if ("STAFF".equals(userType)) {
        return price.multiply(new BigDecimal("0.5"));
    } else {
        return price;
    }
}

// ✅ 策略模式
public interface DiscountStrategy {
    BigDecimal calculate(BigDecimal price);
}

@Component
public class DiscountStrategyFactory {
    private final Map<String, DiscountStrategy> strategyMap;

    public DiscountStrategyFactory() {
        strategyMap = new HashMap<>();
        strategyMap.put("VIP", price -> price.multiply(new BigDecimal("0.8")));
        strategyMap.put("SVIP", price -> price.multiply(new BigDecimal("0.7")));
        strategyMap.put("STAFF", price -> price.multiply(new BigDecimal("0.5")));
    }

    public BigDecimal calculate(String userType, BigDecimal price) {
        return strategyMap.getOrDefault(userType, p -> p).calculate(price);
    }
}
```
