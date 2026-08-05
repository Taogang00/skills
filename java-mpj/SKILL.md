---
name: java-mpj
description: 将 MyBatis XML 中的简单单表/非聚合查询改写为 MyBatis-Plus-Join(MPJ) 的 Java Wrapper 写法，消除冗余 XML；复杂聚合类（group by/having/union/CTE 等）查询保留在 XML。当用户要求“去掉 mapper xml”“把 xml 查询改成 MPJ / MyBatisPlusJoin”“简化 mapper xml”“XML 转 Wrapper”“MPJ 改造”时使用。
metadata:
  version: 1.0.0
  author: TaoGang
---

# MyBatis XML → MyBatis-Plus-Join 改造

把 XML 里的「简单单表查询」和「非聚合连表查询」改写为 MPJ 的 Wrapper 写法，消除冗余 XML；复杂聚合查询保留 XML。

对应 `java-dev` 规范：**简单的单表、联表查询使用 MybatisPlus + MybatisPlusJoin 实现即可，不需要自定义 Mapper 接口和写 xml 映射文件，减少冗余代码。**

## 一、前置约定

改造前先确认目标项目的基类与分页类，**以目标项目现有代码为准**。本文示例基于 `guanwei-boot-starter-mybatis`：

| 用途 | 类型 |
| --- | --- |
| Mapper 基类 | `com.guanwei.mybatis.base.mapper.MBaseMapper<T>` |
| Service 接口基类 | `com.guanwei.mybatis.base.service.MBaseService<T>` |
| Service 实现基类 | `com.guanwei.mybatis.base.service.MBaseServiceImpl<M, T>` |
| 分页查询入参 | `com.guanwei.mybatis.model.PageQuery` |
| 分页可选入参 | `com.guanwei.mybatis.model.PageOptionalQuery` |

> 注意：分页基类是 `com.guanwei.mybatis.model.PageQuery`，不要误用其他同名类。以项目中已有 `XxxPageQuery` 的 import 为准。

关键机制：`selectJoinPage(PageQuery, Class, wrapper)` **返回 `List`（实际 `PageList`）而非 `IPage`**。分页由拦截器完成，总数由 ResponseBodyAdvice 注入响应，业务代码不需要处理 total、不要手写 count 和 limit。

## 二、改造范围判定

逐条 `<select>` 判定，不要整个文件一刀切。同一个 XML 可以「部分改造 + 部分保留」。

### 应当改造

- 单表查询，条件为 `=`/`in`/`like`/`between`/范围比较，配合 `<if>` 动态拼接
- 非聚合的 `left join` / `inner join`，字段平铺或一对一 / 一对多映射
- `resultMap` 中只有 `<result>` / `<association>` / `<collection>` 的映射
- 简单 `order by`、分页
- **单表的简单聚合**：整表或简单条件下的 `count/sum/max/min/avg`，无 `group by`。MPJ 有 `selectCount/selectSum/selectMax/selectMin/selectAvg/selectFunc` 支持（见下方示例 6）

### 保留 XML

- `group by` + `having` 的分组统计
- 窗口函数、`union`/`union all`、`with` CTE、递归查询
- 派生表 / 子查询作为 `from` 来源、复杂相关子查询
- 大段 `case when` 行转列、动态表名、方言特有语法、存储过程
- 批量 `insert`/`update` 的 `<foreach>`

> 两个边界澄清：
> 1. 分页查询最外层的 `count(*)` **不算聚合**，拦截器会自动生成 count 语句，可以改造。
> 2. 聚合 ≠ 必须留 XML。判断依据是**有没有 `group by`/`having`**，单表无分组的聚合用 `selectFunc` 系列即可。

### 必须先问用户

- 单个 `<select>` 同时包含可改造和必须保留的特征
- XML 中的表/字段在项目里找不到对应实体类
- SQL 依赖手写别名且上层按别名取值，改造可能影响调用方
- 该 statement 被多处调用，改造范围不清晰

## 三、改造示例（XML 前 → MPJ 后）

### 示例 1：单表全量 / 条件查询

改造前：

```java
// UserMapper.java
List<UserDTO> getUserList(UserPageQuery query);
```

```xml
<select id="getUserList" resultType="com.guanwei.mybatis.dto.UserDTO">
    select * from UserInfo
    <where>
        <if test="name != null and name != ''">
            and name like concat(#{name}, '%')
        </if>
        <if test="phone != null and phone != ''">
            and phone = #{phone}
        </if>
    </where>
    order by id desc
</select>
```

改造后（删除 Mapper 方法和 XML，单表用 MP 原生 Wrapper 即可）：

```java
List<User> list = userService.list(Wrappers.<User>lambdaQuery()
        .likeRightIfExists(User::getName, query.getName())
        .eqIfExists(User::getPhone, query.getPhone())
        .orderByDesc(User::getId));
```

要点：`<if>` 不再需要手写 `StrUtil.isNotBlank(...)` 之类的 boolean 判断，MPJ 提供 **`xxIfExists` 系列方法**，自动判断值是否为空，仅当非空才拼接条件。这是消除动态 SQL 的关键。

| XML | MPJ（推荐 xxIfExists） |
| --- | --- |
| `<if test="name != null and name != ''">and name like concat(#{name},'%')</if>` | `.likeRightIfExists(X::getName, name)` |
| `<if test="phone != null and phone != ''">and phone = #{phone}</if>` | `.eqIfExists(X::getPhone, phone)` |
| `<if test="list != null and list.size() > 0">and id in ...</if>` | `.inIfNotEmpty(X::getId, list)` |
| `<if test="start != null">and date &gt;= #{start}</if>` | `.geIfExists(X::getDate, start)` |

> **不要用** `.likeRight(StrUtil.isNotBlank(name), X::getName, name)` 这种手动 boolean 首参的写法——`xxIfExists` 已内置空值判断，更简洁且不易漏判。若必须保留手动判断（如自定义复杂条件），可用 `wrapper.eq(condition, ...)` 形式，但优先用 `xxIfExists`。

### IfExists 系列完整用法

`xxIfExists` 自动判断条件值是否为空（非空才拼接），替代所有 `if (x != null) wrapper.eq(...)` 与 `wrapper.eq(condition, ...)` 的手动布尔判断。

> 版本说明：`xxIfExists` 在较新的 MPJ 版本引入，不同小版本支持的方法集合略有差异，以项目实际依赖的 `mybatis-plus-join` 版本为准（本项目由 `guanwei-boot-dependencies:3.0.0-SNAPSHOT` 的 BOM 管理）。若当前版本不支持某个 `xxIfExists` 方法，回退写法是用条件方法的 boolean 首参：`eq(condition, X::getF, val)` / `in(CollUtil.isNotEmpty(list), X::getId, list)`。

- **支持的方法**：`eqIfExists` / `neIfExists` / `gtIfExists` / `geIfExists` / `ltIfExists` / `leIfExists` / `likeIfExists` / `notLikeIfExists` / `likeLeftIfExists` / `likeRightIfExists` 等，一一对应原条件方法；较新版本还提供 `betweenIfExists(字段, v1, v2)`、`inIfNotEmpty(字段, Collection)` 等。具体可用方法以依赖版本为准。
- **判断策略（决定何为"空"）**，默认 `NOT_EMPTY`：
  - `NOT_EMPTY`（默认）：String 用 `isNotEmpty`（长度>0），其他用 `Objects.nonNull`
  - `NOT_BLANK`：String 用 `isNotBlank`（排除纯空格/换行），其他用 `Objects.nonNull`
  - `NOT_NULL`：全部用 `Objects.nonNull`
- **局部指定策略**：`wrapper.setIfExists(IfExistsEnum.NOT_BLANK)`
- **全局配置**：`application.yml` 中 `mybatis-plus-join: if-exists: not_empty`

改造参考（分页条件查询，连表 DTO 同样适用，主表/从表字段都能用）：

```java
@GetMapping("/list")
public R<?> list(@Validated SaHolidayPageQuery query) {
    MPJLambdaWrapper<SaHoliday> lambdaQueryWrapper = JoinWrappers.lambda(SaHoliday.class);
    lambdaQueryWrapper.selectAll(SaHoliday.class);
    lambdaQueryWrapper.eqIfExists(SaHoliday::getHyId, query.getHyId());
    lambdaQueryWrapper.eqIfExists(SaHoliday::getYear, query.getYear());
    lambdaQueryWrapper.eqIfExists(SaHoliday::getName, query.getName());
    lambdaQueryWrapper.eqIfExists(SaHoliday::getOrderNo, query.getOrderNo());
    lambdaQueryWrapper.orderByAsc(SaHoliday::getYear);
    lambdaQueryWrapper.orderByAsc(SaHoliday::getOrderNo);
    List<SaHolidayListDTO> list = saHolidayService.selectJoinPage(query, SaHolidayListDTO.class, lambdaQueryWrapper);
    return R.OK(list);
}
```

### 示例 1.1：纯 `selectAll` + 条件过滤转 DTO 的字段映射规则（重点）

上面这种「只 `selectAll(主表)` + `eqIfExists` 过滤、不连表」的查询，是 MPJ 最常见的单表条件查询写法。`selectJoinList/selectJoinPage` 把结果映射到目标 DTO 时遵循一条关键规则：

> **结果集中的列名按「属性名」自动匹配并填充 DTO 字段；DTO 里凡是要在结果中接收数据的属性，其 getter/setter 对应的属性名必须与 SQL 查询出的列名一致，否则该字段为 null。**

结合 MPJ 的机制具体注意：

- `selectAll(SaHoliday.class)` 产出的是 `sa_holiday.*`，列名即主表字段名（如 `hy_id`、`year`、`name`、`order_no`）。MPJ 会自动把下划线列名转成驼峰属性名（`hyId`、`year`、`name`、`orderNo`）去匹配 `SaHolidayListDTO` 的属性。
- 因此 **`SaHolidayListDTO` 的字段定义要与 `SaHoliday` 实体字段一一对应**（或只取需要的子集，子集内字段名/类型保持一致）。只要 DTO 有对应属性且类型兼容，就会被自动填充，**不需要任何 `@TableField`/`resultMap` 配置**。
- **字段名/类型不一致时必须用 `selectAs` 对齐**（不要指望自动映射会"巧合"命中）。例如 DTO 想叫 `holidayName` 而表字段是 `name`：
  ```java
  // 列名->DTO 属性名不一致，用 selectAs 显式对齐（map 到 DTO 的 getHolidayName）
  lambdaQueryWrapper.selectAs(SaHoliday::getName, SaHolidayListDTO::getHolidayName);
  // 过滤条件仍按实体字段写，与 DTO 叫什么无关
  lambdaQueryWrapper.eqIfExists(SaHoliday::getName, query.getName());
  ```
  > 注意：`selectAs(源字段, DTO::getXxx)` 的语义是「把源字段的值映射/别名到 DTO 的 getXxx」。当只对个别列改名时，常与 `selectAll` 搭配；若**全部列都需要改名或只取部分列**，应改用逐个 `selectAs(...)` 而非 `selectAll`，避免 `selectAll` 带出的列在 DTO 里找不到对应属性而被丢弃、或列名与 DTO 属性对不上。项目常见做法是整段用 `selectAs` 逐列指定（见 `SaSscChargeStationViewDTO`）。
- `eqIfExists` 这类**过滤条件只影响 where，不影响 select 列与 DTO 映射**；它写的是实体字段（`SaHoliday::getName`），与 DTO 叫什么无关。
- 这种单表场景也可直接用 MP 原生 `Wrappers.lambdaQuery()` + `list()/page()`；用 `selectJoinPage` 的目的通常是为了统一走 DTO（如 `SaHolidayListDTO`）返回，保持 `resultType=DTO` 的等价写法。

自检：DTO 接收的字段名是否与 `selectAll`/`selectAs` 产出的列（驼峰属性名）一致？有不一致的是否都用了 `selectAs` 显式对齐？

### 示例 2：连表 + 字段别名

改造前：

```xml
<select id="getUserList" resultType="com.guanwei.mybatis.dto.UserDTO">
    select t.*, r.name as roleName
    from UserInfo t
    left join userrole ur on ur.userid = t.id
    left join role r on r.id = ur.roleid
    where t.id = #{id}
</select>
```

改造后：

```java
MPJLambdaWrapper<User> wrapper = JoinWrappers.lambda(User.class)
        .selectAll(User.class)
        .selectAs(Role::getName, UserDTO::getRoleName)
        .leftJoin(UserRole.class, UserRole::getUserId, User::getId)
        .leftJoin(Role.class, Role::getId, UserRole::getRoleId)
        .eq(User::getId, id);

List<UserDTO> list = userMapper.selectJoinList(UserDTO.class, wrapper);
```

要点：
- `JoinWrappers.lambda(主表.class)` 起手，主表即原 SQL 的 `from` 表
- `selectAll(X.class)` → `x.*`；`selectAs(源字段, DTO::getXxx)` → `as` 别名
- `leftJoin(从表.class, 从表关联字段, 主表关联字段)` — **从表字段在前**
- 同表关联多次必须显式别名：`.leftJoin(Role.class, "r2", Role::getId, X::getRoleId)`

### 示例 3：association 一对一

改造前：

```xml
<resultMap id="UserRoleMap" type="com.guanwei.mybatis.dto.UserRoleDTO">
    <id column="id" property="id"/>
    <result column="name" property="name"/>
    <association property="role" javaType="com.guanwei.mybatis.entity.Role">
        <id column="r_id" property="id"/>
        <result column="r_name" property="name"/>
    </association>
</resultMap>
```

改造后：

```java
MPJLambdaWrapper<User> wrapper = JoinWrappers.lambda(User.class)
        .selectAll(User.class)
        .selectAssociation(Role.class, UserRoleDTO::getRole, role -> role   // 带字段级映射
                .id(Role::getId, RoleDTO::getId)
                .result(Role::getName, RoleDTO::getName))
        .leftJoin(UserRole.class, UserRole::getUserId, User::getId)
        .leftJoin(Role.class, Role::getId, UserRole::getRoleId);

List<UserRoleDTO> list = userService.selectJoinList(UserRoleDTO.class, wrapper);
```

> `selectAssociation`(一对一) 与 `selectCollection`(一对多) 用法完全对称：`.id()` 指定关联对象主键、`.result()` 指定其余属性，都支持继续嵌套 `collection`/`association`。区别只在目标 DTO 字段类型：一个是单对象（`RoleDTO`），一个是 `List`（如 `List<RoleDTO>`）。项目实际用法（如 `SaSscChargeStationViewDTO` 内嵌 `SaSscOperatorViewDTO`）即采用此带 builder 的写法。

### 示例 4：collection 一对多（含 N+1 消除）

改造前（`<collection>` 嵌套 select，存在 N+1 查询）：

```xml
<resultMap id="UserRoleDtoMap" type="com.guanwei.mybatis.dto.UserRoleDTO">
    <id column="id" property="id"/>
    <result column="name" property="name"/>
    <collection property="roles" column="id"
                ofType="com.guanwei.mybatis.entity.Role" select="getRole"/>
</resultMap>

<select id="getRole" resultType="com.guanwei.mybatis.entity.Role">
    select a.* from role a
    inner join userrole b on a.id = b.roleid
    where b.userid = #{id}
</select>

<select id="getUserRole" resultMap="UserRoleDtoMap">
    select * from UserInfo
</select>
```

改造后（一条 SQL 搞定，顺带消除 N+1）：

```java
MPJLambdaWrapper<User> wrapper = JoinWrappers.lambda(User.class)
        .selectAll(User.class)
        .selectCollection(Role.class, UserRoleDTO::getRoles)
        .leftJoin(UserRole.class, UserRole::getUserId, User::getId)
        .leftJoin(Role.class, Role::getId, UserRole::getRoleId);

List<UserRoleDTO> list = userService.selectJoinList(UserRoleDTO.class, wrapper);
```

集合字段级自定义映射：

```java
.selectCollection(Role.class, UserRoleCustomDTO::getRoles, role -> role
        .id(Role::getId)
        .result(Role::getName, RoleNameDTO::getRoleName))
```

映射标量集合（如只要 id 列表 `List<String>`）：

```java
.selectCollection(Role.class, UserRoleIdsDTO::getRoleIds, role -> role.result(Role::getId))
```

嵌套集合（用户 → 角色 → 权限）：

```java
.selectCollection(Role.class, UserRolePermissionDTO::getRoles, role -> role
        .id(Role::getId)
        .result(Role::getName)
        .collection(Permission.class, RolePermissionDTO::getPermissions, p -> p
                .id(Permission::getId)
                .result(Permission::getName)))
```

### 示例 4.1：leftJoin 多条件必须放在 `on` 子句（性能要点）

关联查询时，凡是与被关联表相关的**过滤条件**（不只是关联键），都应通过 `leftJoin(从表.class, on -> on.eq(...).eq(...))` 的 lambda 形式写进 `on` 子句，**不要**把第二个/后续条件拆到 `where` 后面。

理由：写在 `on` 里会在**连接之前**就按条件过滤从表数据，减少参与 join 的行数；写到 `where` 里则是先全量连表、再对结果集过滤，连接数据量更大、效率更低。尤其是从表数据量大、或按业务类型（如 `materialCode`）筛选时，差异明显。

改造前（错误写法 —— 把过滤条件漏到 where）：

```java
MPJLambdaWrapper<SaPetrolStationApply> wrapper = JoinWrappers.lambda(SaPetrolStationApply.class)
        .selectAll(SaPetrolStationApply.class)
        .selectCollection(SaMaterialApply.class, SaPetrolStationFormDTO::getMaterials, ...)
        .leftJoin(SaMaterialApply.class, SaMaterialApply::getBizObjectId, SaPetrolStationApply::getPsaId)
        .eq(SaMaterialApply::getMaterialCode, EnumMaterialCode.JYZ.getValue()) // ❌ 放在 where，先全量连表再过滤
        .eq(SaPetrolStationApply::getApplyId, applyId);
```

改造后（正确写法 —— 过滤条件进 `on`）：

```java
MPJLambdaWrapper<SaPetrolStationApply> wrapper = JoinWrappers.lambda(SaPetrolStationApply.class)
        .selectAll(SaPetrolStationApply.class)
        .selectCollection(SaMaterialApply.class, SaPetrolStationFormDTO::getMaterials, material -> material
                .id(SaMaterialApply::getMaterialId, SaMaterialFormDTO::getMaterialId)
                .result(SaMaterialApply::getMaterialName, SaMaterialFormDTO::getMaterialName)
                .result(SaMaterialApply::getMaterialCode, SaMaterialFormDTO::getMaterialCode)
                .result(SaMaterialApply::getMaterialType, SaMaterialFormDTO::getMaterialType)
                .result(SaMaterialApply::getOrderNo, SaMaterialFormDTO::getOrderNo)
                .result(SaMaterialApply::getBizObjectId, SaMaterialFormDTO::getBizObjectId)
                .collection(SaAttachmentApply.class, SaMaterialFormDTO::getAttachments, attachment -> attachment
                        .id(SaAttachmentApply::getAttachId, SaAttachmentFormDTO::getAttachId)
                        .result(SaAttachmentApply::getFileName, SaAttachmentFormDTO::getFileName)
                        .result(SaAttachmentApply::getFileType, SaAttachmentFormDTO::getFileType)
                        .result(SaAttachmentApply::getFilePath, SaAttachmentFormDTO::getFilePath)
                        .result(SaAttachmentApply::getMaterialId, SaAttachmentFormDTO::getMaterialId)
                )
        )
        .leftJoin(SaMaterialApply.class, on -> on                                  // ✅ 关联键 + 过滤条件都在 on
                .eq(SaMaterialApply::getBizObjectId, SaPetrolStationApply::getPsaId)
                .eq(SaMaterialApply::getMaterialCode, EnumMaterialCode.JYZ.getValue()))
        .leftJoin(SaAttachmentApply.class, SaAttachmentApply::getMaterialId, SaMaterialApply::getMaterialId)
        .eq(SaPetrolStationApply::getApplyId, applyId);

return saPetrolStationApplyService.selectJoinList(SaPetrolStationFormDTO.class, wrapper);
```

要点：
- `leftJoin(从表.class, on -> on.eq(a).eq(b))` 用 lambda 形式可写任意多个 `on` 条件；**凡是作用于被关联表的过滤条件都进 `on`**。
- `where`（`wrapper.eq(...)` 在 join 之外）只保留**主表自身的过滤条件**（如示例中的 `applyId`）。
- 注意区分：`on` 里放的是「针对被关联表的过滤」，主表本身的过滤放 `where` 即可。
- 多级嵌套时，下一层 `leftJoin`（如 `SaAttachmentApply`）若也有针对附件表的过滤，同样写进该层的 `on`。


### 示例 5：分页查询

改造前：

```xml
<select id="getUserPage" resultType="com.guanwei.mybatis.dto.UserDTO">
    select t.*, r.name as roleName
    from UserInfo t
    left join role r on r.id = t.roleid
    <where>
        <if test="name != null and name != ''">and t.name like concat(#{name}, '%')</if>
    </where>
    order by t.id desc
    limit #{offset}, #{pageSize}
</select>

<select id="getUserPageCount" resultType="int">
    select count(1) from UserInfo t ...
</select>
```

改造后（不写 count、不写 limit）：

```java
public List<UserDTO> page(UserPageQuery query) {   // UserPageQuery extends PageQuery
    MPJLambdaWrapper<User> wrapper = JoinWrappers.lambda(User.class)
            .selectAll(User.class)
            .selectAs(Role::getName, UserDTO::getRoleName)
            .leftJoin(Role.class, Role::getId, User::getRoleId)
            .likeRightIfExists(User::getName, query.getName())
            .orderByDesc(User::getId);

    return userService.selectJoinPage(query, UserDTO.class, wrapper);
}
```

要点：
- 分页参数不要手动 `setPage/setPageSize`，也不要 new Page
- 不传分页参数就查全量的场景，入参继承 `PageOptionalQuery`
- `like` 若用户输入可能含 `%`/`_`，在查询对象字段上加 `@EscapeWildcard`

### 示例 6：单表简单聚合（可以改造）

改造前：

```xml
<select id="getUserCount" resultType="java.lang.Integer">
    select count(1) from UserInfo
</select>
```

改造后：

```java
Long count = userService.count(Wrappers.<User>lambdaQuery().eq(User::getUserState, 1));
```

多个聚合值一次取出：

```java
MPJLambdaWrapper<User> wrapper = JoinWrappers.lambda(User.class)
        .selectSum(User::getUserState, UserStatisticsDTO::getTotal)
        .selectMax(User::getUserState, UserStatisticsDTO::getMaximum)
        .selectMin(User::getUserState, UserStatisticsDTO::getMinimum)
        .selectAvg(User::getUserState, UserStatisticsDTO::getAverage);

UserStatisticsDTO dto = userMapper.selectJoinOne(UserStatisticsDTO.class, wrapper, false);
```

自定义函数 / 表达式：

```java
// CASE WHEN
.selectFunc(() -> "CASE %s WHEN 1 THEN '是' ELSE '否' END",
        User::getUserState, UserStatisticsDTO::getStatus)

// 多字段拼接
.selectFunc("concat(%s, %s)",
        columns -> columns.accept(User::getName, User::getPhone),
        UserStatisticsDTO::getFullName)

// 带参数占位符
.selectFunc("CASE WHEN %s IS NULL THEN {0} ELSE {1} END",
        columns -> columns.accept(User::getPhone).values("空", "非空"),
        UserStatisticsDTO::getStatus)
```

### 示例 7：保留 XML 的情况（不要改）

带 `group by` + `having` 的分组统计，保留：

```xml
<select id="getRoleUserStat" resultType="com.guanwei.mybatis.dto.RoleStatDTO">
    select r.id as roleId, r.name as roleName,
           count(1) as userCount, sum(t.score) as totalScore
    from UserInfo t
    left join role r on r.id = t.roleid
    group by r.id, r.name
    having count(1) > #{minCount}
</select>
```

## 四、执行流程

1. **列清单**：列出 XML 所有 statement，逐条标注 `改造` / `保留` / `待确认`，先给用户看
2. **提问**：把待确认项逐条问清楚再动手
3. **逐条改造**：一次改一个 statement，不要批量重写整个文件
4. **同步调用方**：改 Mapper 方法签名后同步所有调用点
5. **清理 XML**：删除已迁移的 `<select>`，以及**仅**被它使用的 `resultMap` / `<sql>`；文件内 statement 全部迁走则删除文件，并检查 `mapper-locations` 配置
6. **自检**：对照下方清单

## 五、自检清单

- [ ] `group by`/`having` 的分组统计是否仍留在 XML？
- [ ] `leftJoin` 参数顺序是否为「从表字段在前，主表字段在后」？
- [ ] `leftJoin` 的**过滤条件**是否写进 `on` 子句（lambda 形式），而非漏到 `where` 后面？（性能要点，见示例 4.1）
- [ ] 每个 `<if>` 是否都转成 `xxIfExists` 系列方法（而非手写 `StrUtil.isNotBlank(...)` 之类的 boolean 首参）？
- [ ] `and`/`or` 优先级是否保持？（`or` 混用需 `.and(w -> ...)` 包裹）
- [ ] DTO 字段与 `selectAll`(驼峰属性名)/`selectAs` 目标是否一一对应，无遗漏？纯 `selectAll` 场景 DTO 字段是否与主表字段名一致，不一致的是否用 `selectAs` 显式对齐？
- [ ] 分页是否走 `selectJoinPage(query, DTO.class, wrapper)`，未手写 count/limit？
- [ ] 被删除的 `resultMap`/`<sql>` 是否确实无其他 statement 引用？
- [ ] 所有调用点是否已同步更新？
- [ ] 是否遵守 `java-dev` 规范：只用 DTO（不建 VO/BO）、不改代码生成器产出的模板代码？

## 六、常见错误

```java
// 错误：leftJoin 参数顺序反了
.leftJoin(Role.class, User::getRoleId, Role::getId)
// 正确：从表字段在前
.leftJoin(Role.class, Role::getId, User::getRoleId)

// 错误：丢掉 <if>，条件变成无条件生效
.eq(User::getUserState, query.getUserState())
// 不推荐：保留动态判断，但手写 boolean（冗长易漏判）
.eq(query.getUserState() != null, User::getUserState, query.getUserState())
// 推荐：用 xxIfExists，自动判空，无需手写 if 判断
.eqIfExists(User::getUserState, query.getUserState())

// 错误：手动分页，与框架拦截器重复
wrapper.last("limit " + query.getPage() * query.getPageSize());
// 正确：交给框架
userService.selectJoinPage(query, UserDTO.class, wrapper);

// 错误：以为 selectJoinPage 返回 IPage
IPage<UserDTO> page = userService.selectJoinPage(query, UserDTO.class, wrapper);
// 正确：返回 List，total 由框架注入响应
List<UserDTO> list = userService.selectJoinPage(query, UserDTO.class, wrapper);

// 错误：把被关联表的过滤条件写到 where，先全量连表再过滤，连接数据量大、效率低
.leftJoin(SaMaterialApply.class, SaMaterialApply::getBizObjectId, SaPetrolStationApply::getPsaId)
.eq(SaMaterialApply::getMaterialCode, EnumMaterialCode.JYZ.getValue())
// 正确：被关联表的过滤条件一并写进 on，连接前即过滤，减少参与 join 的行数
.leftJoin(SaMaterialApply.class, on -> on
        .eq(SaMaterialApply::getBizObjectId, SaPetrolStationApply::getPsaId)
        .eq(SaMaterialApply::getMaterialCode, EnumMaterialCode.JYZ.getValue()))
```
