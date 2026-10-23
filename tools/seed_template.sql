-- The starter database's tables, as the app's Room database creates them, and the rows the app
-- puts in a new database itself (the dummy publisher and series, My Collection and the Wish List).
-- tools/build_seed_from_db.py fills a copy of this. When the app's Room schema changes, this has to
-- be made again from a database the new app created: tools/make_seed_template.py DB.

CREATE TABLE `Appearance` (`appearanceId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `story` INTEGER NOT NULL, `character` INTEGER NOT NULL, `details` TEXT, `notes` TEXT, `membership` TEXT, `issue` INTEGER NOT NULL, `series` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`story`) REFERENCES `Story`(`storyId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`character`) REFERENCES `Character`(`characterId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`series`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `BondType` (`bondTypeId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `description` TEXT NOT NULL, `notes` TEXT, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `Brand` (`brandId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `yearBegan` TEXT, `yearEnded` TEXT, `notes` TEXT, `url` TEXT, `issueCount` INTEGER NOT NULL, `yearBeganUncertain` INTEGER NOT NULL, `yearEndedUncertain` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `Character` (`characterId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `alterEgo` TEXT, `publisher` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`publisher`) REFERENCES `Publisher`(`publisherId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `CollectionItem` (`collectionItemId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `issue` INTEGER NOT NULL, `series` INTEGER NOT NULL, `userCollection` INTEGER NOT NULL, `storageLocation` TEXT, `condition` TEXT, `notes` TEXT, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`series`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`userCollection`) REFERENCES `UserCollection`(`userCollectionId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `CopySigner` (`collectionItem` INTEGER NOT NULL, `creator` INTEGER NOT NULL, PRIMARY KEY(`collectionItem`, `creator`), FOREIGN KEY(`collectionItem`) REFERENCES `CollectionItem`(`collectionItemId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`creator`) REFERENCES `Creator`(`creatorId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `Cover` (`coverId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `issue` INTEGER NOT NULL, `coverUri` TEXT, `markedDelete` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `Creator` (`creatorId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `sortName` TEXT NOT NULL, `bio` TEXT, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `Credit` (`creditId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `story` INTEGER NOT NULL, `nameDetail` INTEGER NOT NULL, `role` INTEGER NOT NULL, `issue` INTEGER, `series` INTEGER, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`story`) REFERENCES `Story`(`storyId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`nameDetail`) REFERENCES `NameDetail`(`nameDetailId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`role`) REFERENCES `Role`(`roleId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`series`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `ExCredit` (`creditId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `story` INTEGER NOT NULL, `nameDetail` INTEGER NOT NULL, `role` INTEGER NOT NULL, `issue` INTEGER, `series` INTEGER, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`story`) REFERENCES `Story`(`storyId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`nameDetail`) REFERENCES `NameDetail`(`nameDetailId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`role`) REFERENCES `Role`(`roleId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`series`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `Issue` (`issueId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `series` INTEGER NOT NULL, `issueNum` INTEGER NOT NULL, `releaseDate` TEXT, `upc` INTEGER, `variantName` TEXT NOT NULL, `variantOf` INTEGER, `sortCode` INTEGER NOT NULL, `coverDateLong` TEXT, `onSaleDateUncertain` INTEGER NOT NULL, `coverDate` TEXT, `notes` TEXT, `brandId` INTEGER, `issueNumRaw` TEXT, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`series`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`variantOf`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `NameDetail` (`nameDetailId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `creator` INTEGER NOT NULL, `name` TEXT NOT NULL, `sortName` TEXT, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`creator`) REFERENCES `Creator`(`creatorId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `Publisher` (`publisherId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `publisher` TEXT NOT NULL, `yearBegan` TEXT, `yearBeganUncertain` INTEGER NOT NULL, `yearEnded` TEXT, `yearEndedUncertain` INTEGER NOT NULL, `url` TEXT, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `Role` (`roleId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `roleName` TEXT NOT NULL, `sortOrder` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `Series` (`seriesId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `seriesName` TEXT NOT NULL, `sortName` TEXT, `volume` INTEGER NOT NULL, `publisher` INTEGER NOT NULL, `startDate` TEXT, `endDate` TEXT, `description` TEXT, `publishingFormat` TEXT, `firstIssue` INTEGER, `notes` TEXT, `issueCount` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`publisher`) REFERENCES `Publisher`(`publisherId`) ON UPDATE NO ACTION ON DELETE CASCADE );
CREATE TABLE `SeriesBond` (`bondId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `origin` INTEGER NOT NULL, `target` INTEGER NOT NULL, `originIssue` INTEGER, `targetIssue` INTEGER, `bondType` INTEGER NOT NULL, `notes` TEXT, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`origin`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`target`) REFERENCES `Series`(`seriesId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`originIssue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`targetIssue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE CASCADE , FOREIGN KEY(`bondType`) REFERENCES `BondType`(`bondTypeId`) ON UPDATE NO ACTION ON DELETE RESTRICT );
CREATE TABLE `Story` (`storyId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `storyType` INTEGER NOT NULL, `title` TEXT, `feature` TEXT, `characters` TEXT, `synopsis` TEXT, `notes` TEXT, `sequenceNumber` INTEGER NOT NULL, `issue` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL, FOREIGN KEY(`storyType`) REFERENCES `StoryType`(`storyTypeId`) ON UPDATE NO ACTION ON DELETE NO ACTION , FOREIGN KEY(`issue`) REFERENCES `Issue`(`issueId`) ON UPDATE NO ACTION ON DELETE NO ACTION );
CREATE TABLE `StoryType` (`storyTypeId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `sortCode` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL);
CREATE TABLE `UserCollection` (`userCollectionId` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `permanent` INTEGER NOT NULL, `lastUpdated` TEXT NOT NULL);
CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT);
CREATE INDEX `index_Appearance_character` ON `Appearance` (`character`);
CREATE INDEX `index_Appearance_issue` ON `Appearance` (`issue`);
CREATE INDEX `index_Appearance_series` ON `Appearance` (`series`);
CREATE INDEX `index_Appearance_story` ON `Appearance` (`story`);
CREATE INDEX `index_Character_alterEgo` ON `Character` (`alterEgo`);
CREATE INDEX `index_Character_name` ON `Character` (`name`);
CREATE INDEX `index_Character_publisher` ON `Character` (`publisher`);
CREATE UNIQUE INDEX `index_CollectionItem_issue_userCollection` ON `CollectionItem` (`issue`, `userCollection`);
CREATE INDEX `index_CollectionItem_series` ON `CollectionItem` (`series`);
CREATE INDEX `index_CollectionItem_userCollection` ON `CollectionItem` (`userCollection`);
CREATE INDEX `index_CopySigner_creator` ON `CopySigner` (`creator`);
CREATE UNIQUE INDEX `index_Cover_issue` ON `Cover` (`issue`);
CREATE INDEX `index_Creator_name` ON `Creator` (`name`);
CREATE INDEX `index_Creator_sortName` ON `Creator` (`sortName`);
CREATE INDEX `index_Credit_issue` ON `Credit` (`issue`);
CREATE INDEX `index_Credit_nameDetail` ON `Credit` (`nameDetail`);
CREATE INDEX `index_Credit_role` ON `Credit` (`role`);
CREATE INDEX `index_Credit_series` ON `Credit` (`series`);
CREATE INDEX `index_Credit_story` ON `Credit` (`story`);
CREATE UNIQUE INDEX `index_Credit_story_nameDetail_role` ON `Credit` (`story`, `nameDetail`, `role`);
CREATE INDEX `index_ExCredit_issue` ON `ExCredit` (`issue`);
CREATE INDEX `index_ExCredit_nameDetail` ON `ExCredit` (`nameDetail`);
CREATE INDEX `index_ExCredit_role` ON `ExCredit` (`role`);
CREATE INDEX `index_ExCredit_series` ON `ExCredit` (`series`);
CREATE INDEX `index_ExCredit_story` ON `ExCredit` (`story`);
CREATE UNIQUE INDEX `index_ExCredit_story_nameDetail_role` ON `ExCredit` (`story`, `nameDetail`, `role`);
CREATE INDEX `index_Issue_series_issueNum` ON `Issue` (`series`, `issueNum`);
CREATE INDEX `index_Issue_variantOf` ON `Issue` (`variantOf`);
CREATE INDEX `index_NameDetail_creator` ON `NameDetail` (`creator`);
CREATE INDEX `index_NameDetail_name` ON `NameDetail` (`name`);
CREATE INDEX `index_NameDetail_sortName` ON `NameDetail` (`sortName`);
CREATE INDEX `index_Publisher_publisher` ON `Publisher` (`publisher`);
CREATE INDEX `index_SeriesBond_bondType` ON `SeriesBond` (`bondType`);
CREATE INDEX `index_SeriesBond_origin` ON `SeriesBond` (`origin`);
CREATE INDEX `index_SeriesBond_originIssue` ON `SeriesBond` (`originIssue`);
CREATE INDEX `index_SeriesBond_target` ON `SeriesBond` (`target`);
CREATE INDEX `index_SeriesBond_targetIssue` ON `SeriesBond` (`targetIssue`);
CREATE INDEX `index_Series_publisher` ON `Series` (`publisher`);
CREATE INDEX `index_Series_seriesName` ON `Series` (`seriesName`);
CREATE INDEX `index_Story_issue` ON `Story` (`issue`);
CREATE INDEX `index_Story_storyType` ON `Story` (`storyType`);

INSERT INTO `Publisher` (publisherId, publisher, yearBegan, yearBeganUncertain, yearEnded, yearEndedUncertain, url, lastUpdated) VALUES (2147483647, 'Dummy Publisher', NULL, 1, NULL, 1, NULL, '2026-10-12');
INSERT INTO `Series` (seriesId, seriesName, sortName, volume, publisher, startDate, endDate, description, publishingFormat, firstIssue, notes, issueCount, lastUpdated) VALUES (2147483647, 'Dummy Series', NULL, 1, 2147483647, '-999999999-01-01', '-999999999-01-01', NULL, NULL, NULL, NULL, 0, '2026-10-12');
INSERT INTO `UserCollection` (userCollectionId, name, permanent, lastUpdated) VALUES (1, 'My Collection', 1, '2026-10-12');
INSERT INTO `UserCollection` (userCollectionId, name, permanent, lastUpdated) VALUES (2, 'Wish List', 1, '2026-10-12');

INSERT INTO room_master_table (id, identity_hash) VALUES (42, '9547207247828bfa222b78d92682bea8');
PRAGMA user_version = 3;
