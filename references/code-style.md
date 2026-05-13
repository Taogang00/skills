# 代码风格、注释与OOP规约

## 1. 代码格式规范

| 规则ID | 级别 | 规则 |
|---|---|---|
| F-001 | 【强制】 | 大括号的使用约定：左大括号前不换行，左大括号后换行，右大括号前换行，右大括号后还有 `else` 等代码则不换行 |
| F-002 | 【强制】 | 单行字符数限制不超过 120 个，超出需要换行 |
| F-003 | 【强制】 | 方法参数在定义和传入时，多个参数逗号后边必须加空格 |
| F-004 | 【强制】 | IDE 的 text file encoding 设置为 `UTF-8` |
| F-005 | 【推荐】 | 单个方法的总行数不超过 80 行（不含注释） |
| F-006 | 【推荐】 | 没有必要增加若干空格来使某一行的字符与上一行对应位置的字符对齐 |
| F-007 | 【强制】 | 任何二目、三目运算符的左右两边都需要加一个空格 |

## 2. 注释规范

```java
/**
 * 类注释：描述类的职责、使用场景
 * 复杂类需要说明设计思路
 *
 * @author 作者
 * @since 1.0.0
 */
public class OrderService {

    /**
     * 方法注释（public方法必须有，内部复杂逻辑也需要注释）
     * 描述方法的功能、参数含义、返回值、可能抛出的异常
     *
     * @param orderId 订单ID，不能为null
     * @param userId  操作用户ID
     * @return 支付结果，包含支付单号和状态
     * @throws OrderNotFoundException 订单不存在时抛出
     * @throws BusinessException      订单状态不允许支付时抛出
     */
    public PayResultVO payOrder(Long orderId, Long userId) {
        // 单行注释：在代码上方，而不是行尾（行尾注释用于变量声明）
        // 1. 查询订单信息
        OrderPO order = orderMapper.selectById(orderId);

        // 2. 校验订单状态（只有待支付状态才能支付）
        if (!OrderStatusEnum.PENDING_PAY.getCode().equals(order.getStatus())) {
            throw new BusinessException(ErrorCode.ORDER_STATUS_NOT_ALLOW_PAY);
        }

        // ... 业务逻辑
    }
}
```

### 注释规则要点
- **【强制】** 所有类都必须添加创建者和创建日期
- **【强制】** 方法内部单行注释，在被注释语句上方另起一行，使用 `//` 注释，不要追加在语句右方
- **【强制】** 所有的枚举类型字段必须要有注释，说明每个数据项的用途
- **【推荐】** 代码修改的同时，注释也要进行相应的修改，保持注释和代码同步
- **【推荐】** 注释掉的代码尽量要配合说明，不要无缘无故的注释代码；对于超过两周的注释代码，建议直接删除

## 3. OOP 规约

### 3.1 类设计

```java
// ✅ 工具类：私有构造器 + static方法，防止实例化
public final class DateUtils {
    private DateUtils() {
        throw new IllegalStateException("Utility class");
    }

    public static String format(LocalDateTime dateTime, String pattern) {
        return dateTime.format(DateTimeFormatter.ofPattern(pattern));
    }
}

// ✅ 覆写方法加 @Override，防止笔误
@Override
public String toString() {
    return "User{id=" + id + ", name=" + name + "}";
}

// ✅ 相同参数类型、相同业务含义、相同逻辑的方法，使用重载而非新增方法名
public UserVO getUser(Long userId) { ... }
public UserVO getUser(String email) { ... }
```

### 3.2 集合使用规范

```java
// 【强制】返回空集合，不返回null
public List<UserVO> listUsers(Long deptId) {
    List<UserPO> userList = userMapper.selectByDeptId(deptId);
    if (CollectionUtils.isEmpty(userList)) {
        return Collections.emptyList();   // ✅ 不要 return null
    }
    return userConverter.toVOList(userList);
}

// 【强制】使用entrySet遍历Map，不使用keySet+get
// ❌ 低效写法
for (String key : map.keySet()) {
    String value = map.get(key);  // 二次查找
}
// ✅ 正确写法
for (Map.Entry<String, String> entry : map.entrySet()) {
    String key = entry.getKey();
    String value = entry.getValue();
}

// 【强制】初始化集合时，尽量指定初始容量（避免扩容开销）
// ❌ 不指定容量
List<String> list = new ArrayList<>();

// ✅ 已知数量时指定容量
List<String> list = new ArrayList<>(expectedSize);

// ✅ HashMap：容量 = 预期元素数量 / 0.75 + 1
Map<String, Object> map = new HashMap<>(16);

// 【强制】不要在 foreach 循环里进行元素的 remove/add 操作
// ✅ 需要删除时，使用Iterator或Stream filter
list.removeIf(item -> item.startsWith("test"));

// 【推荐】使用 JDK8 Stream API 替代复杂的 for 循环
List<String> names = userList.stream()
        .filter(user -> user.getAge() > 18)
        .map(UserPO::getName)
        .sorted()
        .collect(Collectors.toList());
```

### 3.3 字符串处理

```java
// 【强制】大量字符串拼接用 StringBuilder，不用 + 拼接
// ❌ 低效：每次+都创建新对象
String result = "";
for (String item : list) {
    result += item + ",";
}

// ✅ 使用 StringBuilder 或 String.join
StringBuilder sb = new StringBuilder();
for (String item : list) {
    sb.append(item).append(",");
}

// 更简洁的写法
String result = String.join(",", list);

// 【强制】字符串比较，常量在前（避免NPE）
// ❌ 可能NPE
if (status.equals("ACTIVE")) { }

// ✅ 常量在前
if ("ACTIVE".equals(status)) { }

// 或使用 Objects.equals
if (Objects.equals(status, "ACTIVE")) { }
```

### 3.4 避免魔法值

```java
// ❌ 错误：魔法值直接出现在代码中
if (order.getStatus() == 2) {
    sendSms(order.getUserId(), "您的订单已发货");
}

// ✅ 正确：使用枚举或常量
public enum OrderStatusEnum {
    PENDING_PAY(1, "待支付"),
    PAID(2, "已支付"),
    SHIPPED(3, "已发货"),
    COMPLETED(4, "已完成"),
    CANCELLED(5, "已取消");

    private final Integer code;
    private final String desc;

    OrderStatusEnum(Integer code, String desc) {
        this.code = code;
        this.desc = desc;
    }
    // getter...
}

// 使用枚举
if (OrderStatusEnum.SHIPPED.getCode().equals(order.getStatus())) {
    sendSms(order.getUserId(), "您的订单已发货");
}
```

## 4. Java8+ 最佳实践

```java
// Optional 处理可能为null的情况
Optional<UserPO> userOpt = userMapper.findById(userId);
UserVO userVO = userOpt
        .map(userConverter::toVO)
        .orElseThrow(() -> new ResourceNotFoundException("用户不存在"));

// LocalDateTime 替代 Date（线程安全且API更友好）
LocalDateTime now = LocalDateTime.now();
LocalDate today = LocalDate.now();
String formatted = now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

// Stream 分组统计
Map<Integer, Long> countByStatus = orderList.stream()
        .collect(Collectors.groupingBy(OrderPO::getStatus, Collectors.counting()));

// CompletableFuture 异步编排
CompletableFuture<UserVO> userFuture = CompletableFuture.supplyAsync(() -> userService.getUser(userId));
CompletableFuture<List<OrderVO>> orderFuture = CompletableFuture.supplyAsync(() -> orderService.listByUser(userId));

CompletableFuture.allOf(userFuture, orderFuture).join();
UserVO user = userFuture.get();
List<OrderVO> orders = orderFuture.get();
```
