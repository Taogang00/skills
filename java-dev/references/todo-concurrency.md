# 并发与线程池规范

## 1. 线程与线程池

| 规则ID | 级别 | 规则 |
|---|---|---|
| C-001 | 【强制】 | 线程资源必须通过线程池提供，不允许在应用中自行显式创建线程 |
| C-002 | 【强制】 | 线程池不允许使用 `Executors` 创建，必须通过 `ThreadPoolExecutor` 手动指定参数 |
| C-003 | 【强制】 | 创建线程或线程池时，必须指定有意义的线程名称，方便出错时排查 |
| C-004 | 【强制】 | 多线程并行处理定时任务时，`Timer` 运行多个 `TimeTask`，只要其中之一没有捕获抛出的异常，其它任务都会自动终止。推荐使用 `ScheduledExecutorService` |
| C-005 | 【强制】 | `SimpleDateFormat` 是线程不安全的，不要定义为 `static` 变量；推荐使用 `DateTimeFormatter`（JDK8+，线程安全） |

### 线程池配置规范

```java
@Configuration
public class ThreadPoolConfig {

    /**
     * IO密集型线程池（数据库查询、网络请求等）
     * 核心线程数 = CPU核心数 * 2
     */
    @Bean("ioThreadPool")
    public ThreadPoolExecutor ioThreadPool() {
        int cpuCores = Runtime.getRuntime().availableProcessors();
        return new ThreadPoolExecutor(
                cpuCores * 2,                           // 核心线程数
                cpuCores * 4,                           // 最大线程数
                60L, TimeUnit.SECONDS,                  // 空闲线程存活时间
                new LinkedBlockingQueue<>(1000),        // 任务队列（有界）
                new ThreadFactoryBuilder()
                        .setNameFormat("io-pool-%d")    // 线程命名
                        .build(),
                new ThreadPoolExecutor.CallerRunsPolicy() // 拒绝策略：调用者线程执行
        );
    }

    /**
     * CPU密集型线程池（复杂计算）
     * 核心线程数 = CPU核心数 + 1
     */
    @Bean("cpuThreadPool")
    public ThreadPoolExecutor cpuThreadPool() {
        int cpuCores = Runtime.getRuntime().availableProcessors();
        return new ThreadPoolExecutor(
                cpuCores + 1,
                cpuCores + 1,
                0L, TimeUnit.MILLISECONDS,
                new LinkedBlockingQueue<>(500),
                new ThreadFactoryBuilder()
                        .setNameFormat("cpu-pool-%d")
                        .build(),
                new ThreadPoolExecutor.AbortPolicy()    // 超限直接拒绝
        );
    }
}
```

### 拒绝策略选择

| 策略 | 行为 | 适用场景 |
|---|---|---|
| `AbortPolicy`（默认） | 抛出 `RejectedExecutionException` | 明确失败，便于发现问题 |
| `CallerRunsPolicy` | 由调用线程执行该任务 | 不允许丢失任务，且可以接受降速 |
| `DiscardPolicy` | 静默丢弃 | 允许丢失（如监控上报） |
| `DiscardOldestPolicy` | 丢弃队列头部最老的任务 | 需要最新数据 |

## 2. 线程安全

### 正确使用 ThreadLocal

```java
// ✅ 正确：使用后及时清理，防止内存泄漏和脏数据
public class UserContext {
    private static final ThreadLocal<Long> USER_ID_HOLDER = new ThreadLocal<>();

    public static void setUserId(Long userId) {
        USER_ID_HOLDER.set(userId);
    }

    public static Long getUserId() {
        return USER_ID_HOLDER.get();
    }

    public static void clear() {
        USER_ID_HOLDER.remove();  // 必须在请求结束时调用
    }
}

// 在Filter/Interceptor中使用
@Override
public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                             Object handler, Exception ex) {
    UserContext.clear();  // 请求结束时清理
}
```

### 锁的使用规范

```java
// 【强制】加锁的代码块工作量尽量小，能锁方法块就不要锁整个方法
// ❌ 锁粒度过大
public synchronized void processOrder(Long orderId) {
    // 大量无需同步的查询操作
    OrderPO order = orderMapper.selectById(orderId);
    UserPO user = userMapper.selectById(order.getUserId());
    // 只有这里需要同步
    inventory.deduct(order.getSkuId(), order.getQuantity());
}

// ✅ 缩小锁范围
public void processOrder(Long orderId) {
    OrderPO order = orderMapper.selectById(orderId);
    UserPO user = userMapper.selectById(order.getUserId());
    synchronized (this) {
        inventory.deduct(order.getSkuId(), order.getQuantity());
    }
}

// 【推荐】使用 ReentrantLock 替代 synchronized（可设置超时、可中断）
private final ReentrantLock lock = new ReentrantLock();

public boolean tryProcess(Long orderId) {
    if (lock.tryLock(3, TimeUnit.SECONDS)) {
        try {
            // 处理逻辑
            return true;
        } finally {
            lock.unlock();  // 必须在finally中释放
        }
    }
    return false;
}
```

### 原子操作与 volatile

```java
// 计数器使用 AtomicInteger/AtomicLong
private final AtomicInteger requestCount = new AtomicInteger(0);

public void handleRequest() {
    requestCount.incrementAndGet();
}

// 状态标志使用 volatile（保证可见性，不保证原子性）
private volatile boolean running = true;

public void stop() {
    running = false;
}

// 线程安全的集合
private final ConcurrentHashMap<String, Object> cache = new ConcurrentHashMap<>();
private final CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>();
```

## 3. 异步处理

```java
// Spring @Async 使用规范
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        // 【强制】必须处理@Async方法中的异常，否则会被静默忽略
        return (throwable, method, params) ->
                log.error("异步方法执行异常, method:{}", method.getName(), throwable);
    }
}

// 使用 @Async
@Service
public class EmailService {
    @Async
    public CompletableFuture<Boolean> sendWelcomeEmail(String email) {
        // 异步发送邮件
        return CompletableFuture.completedFuture(true);
    }
}
```
