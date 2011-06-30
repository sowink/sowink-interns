CREATE TABLE `mall_gift` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL UNIQUE,
    `image` varchar(100) NOT NULL,
    `creator_id` integer NOT NULL,
    `winkcash` integer UNSIGNED NOT NULL,
    `coins` integer UNSIGNED NOT NULL,
    `created` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `mall_gift`
    ADD CONSTRAINT `creator_id_refs_id_44aedd9e` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);

CREATE TABLE `mall_usergift` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `gift_id` integer NOT NULL,
    `creator_id` integer NOT NULL,
    `recipient_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `bought_with` smallint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `mall_usergift`
    ADD CONSTRAINT `creator_id_refs_id_2f664eb5` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `mall_usergift`
    ADD CONSTRAINT `recipient_id_refs_id_2f664eb5` FOREIGN KEY (`recipient_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `mall_usergift`
    ADD CONSTRAINT `gift_id_refs_id_65dc439e` FOREIGN KEY (`gift_id`) REFERENCES `mall_gift` (`id`);

CREATE INDEX `mall_gift_685aee7`
    ON `mall_gift` (`creator_id`);
CREATE INDEX `mall_usergift_3a2c07ae`
    ON `mall_usergift` (`gift_id`);
CREATE INDEX `mall_usergift_685aee7`
    ON `mall_usergift` (`creator_id`);
CREATE INDEX `mall_usergift_32f69dc`
    ON `mall_usergift` (`recipient_id`);
