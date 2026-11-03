-- ============================================================
-- banktt 银行后台管理系统 —— MySQL 8.0 初始化脚本
-- 生成依据：apps/*/models.py 中的 8 个模型（managed = False，数据库优先）
-- 用途：在新环境中创建 bank 库与 8 张业务表，使项目可以直接运行
-- 用法：mysql -u root -p < sql/bank_init.sql
-- 说明：脚本可重复执行（CREATE TABLE IF NOT EXISTS），不会覆盖已有数据
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `bank`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE `bank`;

-- ------------------------------------------------------------
-- 1. sys_user 系统用户表（models.SysUser，managed = False）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_user` (
    `user_id`     INT          NOT NULL AUTO_INCREMENT COMMENT '用户编号（标识列），从1开始，主键',
    `user_name`   VARCHAR(100) NOT NULL                COMMENT '用户名，必填且唯一',
    `pid`         VARCHAR(18)  NOT NULL                COMMENT '身份证号，必填',
    `email`       VARCHAR(100) DEFAULT NULL            COMMENT '邮箱，非必填',
    `mobile`      VARCHAR(20)  NOT NULL                COMMENT '手机号，必填',
    `address`     VARCHAR(200) DEFAULT NULL            COMMENT '地址，非必填',
    `password`    VARCHAR(100) NOT NULL                COMMENT '密码（加密存储），必填',
    `create_time` DATETIME     NOT NULL                COMMENT '创建时间，必填',
    `update_time` DATETIME     DEFAULT NULL            COMMENT '更新时间，非必填',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_user_name` (`user_name`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统用户表';

-- ------------------------------------------------------------
-- 2. sys_role 系统角色表（models.SysRole）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_role` (
    `role_id`     INT          NOT NULL AUTO_INCREMENT COMMENT '角色编号（标识列），从1开始，主键',
    `role_name`   VARCHAR(100) NOT NULL                COMMENT '角色名称，必填',
    `description` VARCHAR(200) DEFAULT NULL            COMMENT '角色描述，非必填',
    PRIMARY KEY (`role_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统角色表';

-- ------------------------------------------------------------
-- 3. sys_menu 系统菜单表（models.SysMenu）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_menu` (
    `menu_id`    INT          NOT NULL AUTO_INCREMENT COMMENT '菜单编号（标识列），从1开始，主键',
    `menu_name`  VARCHAR(100) NOT NULL                COMMENT '菜单名称，必填',
    `menu_url`   VARCHAR(200) DEFAULT NULL            COMMENT '菜单URL，非必填',
    `parent_id`  INT          NOT NULL DEFAULT 0      COMMENT '父菜单ID，默认0表示顶级菜单',
    `sort_order` INT          NOT NULL DEFAULT 0      COMMENT '排序号，默认0',
    `remark`     VARCHAR(200) DEFAULT NULL            COMMENT '备注，非必填',
    PRIMARY KEY (`menu_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统菜单表';

-- ------------------------------------------------------------
-- 4. sys_user_role 用户角色关联表（models.SysUserRole）
--    unique_together = ('user_id', 'role_id') 会生成联合唯一索引
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_user_role` (
    `id`      INT NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
    `user_id` INT NOT NULL                COMMENT '用户ID，关联sys_user表',
    `role_id` INT NOT NULL                COMMENT '角色ID，关联sys_role表',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_user_role` (`user_id`, `role_id`),
    CONSTRAINT `fk_user_role_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_role_role` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户角色关联表';

-- ------------------------------------------------------------
-- 5. sys_role_menu 角色菜单关联表（models.SysRoleMenu）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_role_menu` (
    `id`      INT NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
    `role_id` INT NOT NULL                COMMENT '角色ID，关联sys_role表',
    `menu_id` INT NOT NULL                COMMENT '菜单ID，关联sys_menu表',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`),
    CONSTRAINT `fk_role_menu_role` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_role_menu_menu` FOREIGN KEY (`menu_id`) REFERENCES `sys_menu` (`menu_id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色菜单关联表';

-- ------------------------------------------------------------
-- 6. user_info 客户信息表（models.UserInfo）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_info` (
    `customer_id`   INT          NOT NULL AUTO_INCREMENT COMMENT '客户编号（标识列），从1开始，主键',
    `customer_name` VARCHAR(100) NOT NULL                COMMENT '开户名，必填',
    `pid`           VARCHAR(18)  NOT NULL                COMMENT '身份证号，必填',
    `telephone`     VARCHAR(20)  NOT NULL                COMMENT '联系电话，必填',
    `address`       VARCHAR(200) DEFAULT NULL            COMMENT '居住地址，非必填',
    PRIMARY KEY (`customer_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '客户信息表';

-- ------------------------------------------------------------
-- 7. card_info 银行卡信息表（models.CardInfo）
--    card_id 为字符串主键，非自增
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `card_info` (
    `card_id`     VARCHAR(20)   NOT NULL           COMMENT '卡号，主键',
    `cur_type`    VARCHAR(3)    NOT NULL           COMMENT '货币类型，必填',
    `open_date`   DATETIME      NOT NULL           COMMENT '开户日期，必填',
    `open_money`  DECIMAL(18,2) NOT NULL           COMMENT '开户金额，必填',
    `balance`     DECIMAL(18,2) NOT NULL           COMMENT '余额，必填',
    `password`    VARCHAR(100)  NOT NULL           COMMENT '密码（加密存储），必填',
    `customer_id` INT           NOT NULL           COMMENT '客户编号，外键关联user_info表',
    PRIMARY KEY (`card_id`),
    CONSTRAINT `fk_card_customer` FOREIGN KEY (`customer_id`) REFERENCES `user_info` (`customer_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '银行卡信息表';

-- ------------------------------------------------------------
-- 8. trade_info 交易信息表（models.TradeInfo）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `trade_info` (
    `tid`         INT           NOT NULL AUTO_INCREMENT COMMENT '交易编号（标识列），从1开始，主键',
    `trans_type`  VARCHAR(50)   NOT NULL                COMMENT '交易类型，必填',
    `card_id`     VARCHAR(20)   NOT NULL                COMMENT '银行卡号，必填',
    `trans_date`  DATETIME      NOT NULL                COMMENT '交易日期，必填',
    `trans_money` DECIMAL(18,2) NOT NULL                COMMENT '交易金额，必填',
    `remark`      VARCHAR(200)  DEFAULT NULL            COMMENT '备注，非必填',
    PRIMARY KEY (`tid`),
    CONSTRAINT `fk_trade_card` FOREIGN KEY (`card_id`) REFERENCES `card_info` (`card_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '交易信息表';

-- ------------------------------------------------------------
-- 9. 初始化数据（可重复执行；用于新环境首次启动即可登录）
--    默认账号：admin / admin123 （登录后请立即修改密码）
-- ------------------------------------------------------------
INSERT IGNORE INTO `sys_role` (`role_id`, `role_name`, `description`) VALUES
    (1, '超管',     '超级管理员，拥有全部权限'),
    (2, '大堂经理', '业务与权限管理'),
    (3, '银行柜员', '日常柜面业务');

INSERT IGNORE INTO `sys_menu` (`menu_id`, `menu_name`, `menu_url`, `parent_id`, `sort_order`, `remark`) VALUES
    (1, '客户管理',     '/user/',      0, 1, '客户信息维护'),
    (2, '银行卡管理',   '/card/',      0, 2, '银行卡开户与维护'),
    (3, '交易管理',     '/trade/',     0, 3, '存取款与转账流水'),
    (4, '系统用户',     '/sys_user/',  0, 4, '系统账号维护'),
    (5, '角色管理',     '/role/',      0, 5, '角色维护'),
    (6, '用户角色关联', '/user_role/', 0, 6, '账号与角色绑定');

INSERT IGNORE INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
    (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6);

-- 初始管理员（密码为 pbkdf2 哈希，明文 admin123；请勿直接改写为明文）
INSERT IGNORE INTO `sys_user`
    (`user_id`, `user_name`, `pid`, `email`, `mobile`, `address`, `password`, `create_time`)
VALUES
    (1, 'admin', '110101199001010011', 'admin@example.com', '13800000000', '系统管理员',
     'pbkdf2_sha256$870000$yHjAUR09WQGpz0UbF4anHF$ZGwHjmOJ5TT22PVFkhvekJ7fw1NGFu54dEhqdY+edRk=',
     NOW());

INSERT IGNORE INTO `sys_user_role` (`user_id`, `role_id`) VALUES (1, 1);

SET FOREIGN_KEY_CHECKS = 1;
