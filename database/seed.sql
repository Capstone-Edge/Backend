    -- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
    --
    -- Host: localhost    Database: smart_home_aiot
    -- ------------------------------------------------------
    -- Server version	8.0.45

    /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
    /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
    /*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
    /*!50503 SET NAMES utf8mb4 */;
    /*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
    /*!40103 SET TIME_ZONE='+00:00' */;
    /*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
    /*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
    /*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
    /*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

    --
    -- Dumping data for table `device_types`
    --

    LOCK TABLES `device_types` WRITE;
    /*!40000 ALTER TABLE `device_types` DISABLE KEYS */;
    INSERT INTO `device_types` VALUES (1,'air_conditioner','에어컨','실내 온도, 운전 모드, 풍량, 바람 방향을 제어하는 스마트 에어컨',1,'2026-05-06 07:00:05','2026-05-06 07:00:05'),(2,'light','조명','전원, 밝기, 색상, 색온도, 장면 모드를 제어하는 스마트 조명',1,'2026-05-06 07:00:05','2026-05-06 07:00:05'),(3,'tv','TV','전원, 볼륨, 채널, 앱 실행, 콘텐츠 재생, 입력 소스, 음소거를 제어하는 스마트 TV',1,'2026-05-20 07:57:15','2026-05-20 07:57:23');
    /*!40000 ALTER TABLE `device_types` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `devices`
    --

    LOCK TABLES `devices` WRITE;
    /*!40000 ALTER TABLE `devices` DISABLE KEYS */;
    INSERT INTO `devices` VALUES (1,1,'living_room_aircon','거실 에어컨','living_room',1,'2026-05-06 07:02:15','2026-05-06 07:02:15'),(2,2,'living_room_light','거실 조명','living_room',1,'2026-05-06 07:02:15','2026-05-06 07:02:15'),(3,3,'living_room_tv','거실 TV','living_room',1,'2026-05-20 07:57:15','2026-05-20 07:57:23');
    /*!40000 ALTER TABLE `devices` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `commands`
    --

    LOCK TABLES `commands` WRITE;
    /*!40000 ALTER TABLE `commands` DISABLE KEYS */;
    INSERT INTO `commands` VALUES (1,1,'set_power','air_conditioner.set_power','에어컨 전원 제어','에어컨의 전원을 켜거나 끈다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(2,1,'set_temperature','air_conditioner.set_temperature','에어컨 온도 설정','에어컨의 목표 온도를 설정한다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(3,1,'set_mode','air_conditioner.set_mode','에어컨 운전 모드 설정','에어컨의 운전 모드를 냉방, 난방, 제습, 송풍, 자동 중 하나로 설정한다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(4,1,'set_fan_speed','air_conditioner.set_fan_speed','에어컨 풍량 설정','에어컨의 풍량을 자동, 약, 중, 강 중 하나로 설정한다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(5,1,'set_louver_angle','air_conditioner.set_louver_angle','에어컨 바람 방향 설정','에어컨 루버의 바람 방향을 설정한다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(6,1,'set_timer','air_conditioner.set_timer','에어컨 예약 설정','에어컨의 지연 실행 또는 예약 종료 시간을 설정한다.',1,'2026-05-06 07:03:36','2026-05-06 07:03:36'),(7,2,'set_power','light.set_power','조명 전원 제어','조명의 전원을 켜거나 끈다.',1,'2026-05-06 07:03:45','2026-05-06 07:03:45'),(8,2,'set_brightness','light.set_brightness','조명 밝기 설정','조명의 밝기를 0부터 100 사이의 값으로 설정한다.',1,'2026-05-06 07:03:45','2026-05-06 07:03:45'),(9,2,'set_color','light.set_color','조명 색상 설정','조명의 색상을 변경한다.',1,'2026-05-06 07:03:45','2026-05-06 07:03:45'),(10,2,'set_color_temperature','light.set_color_temperature','조명 색온도 설정','조명의 색온도를 켈빈 단위로 설정한다.',1,'2026-05-06 07:03:45','2026-05-06 07:03:45'),(11,2,'set_scene','light.set_scene','조명 장면 모드 설정','수면, 집중, 영화, 휴식 등 조명 장면 모드를 설정한다.',1,'2026-05-06 07:03:45','2026-05-06 07:03:45'),(12,3,'set_power','tv.set_power','TV 전원 제어','TV의 전원을 켜거나 끈다.',1,'2026-05-20 07:57:15','2026-05-20 07:57:23'),(13,3,'set_volume','tv.set_volume','TV 볼륨 설정','TV의 볼륨을 0부터 100 사이의 값으로 설정한다.',1,'2026-05-20 07:57:15','2026-05-20 07:57:23'),(14,3,'set_channel','tv.set_channel','TV 채널 설정','TV의 채널 번호를 변경한다.',1,'2026-05-20 07:57:15','2026-05-20 07:57:23'),(15,3,'open_app','tv.open_app','TV 앱 실행','Netflix, YouTube, TVING 등 TV 앱을 실행한다.',1,'2026-05-20 07:57:15','2026-05-20 07:57:23'),(16,3,'play_content','tv.play_content','TV 콘텐츠 재생','특정 앱에서 사용자가 요청한 콘텐츠를 재생한다.',1,'2026-05-20 07:57:15','2026-05-20 07:57:23');
    /*!40000 ALTER TABLE `commands` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `command_parameters`
    --

    LOCK TABLES `command_parameters` WRITE;
    /*!40000 ALTER TABLE `command_parameters` DISABLE KEYS */;
    INSERT INTO `command_parameters` VALUES (1,1,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'에어컨 전원 상태. on 또는 off.'),(2,2,'temperature','integer',1,NULL,NULL,16,30,'에어컨 설정 온도. 16도에서 30도 사이.'),(3,3,'mode','string',1,NULL,'[\"cool\", \"heat\", \"dry\", \"fan\", \"auto\"]',NULL,NULL,'에어컨 운전 모드. cool, heat, dry, fan, auto 중 하나.'),(4,4,'fan_speed','string',1,'\"auto\"','[\"auto\", \"low\", \"medium\", \"high\"]',NULL,NULL,'에어컨 풍량. auto, low, medium, high 중 하나.'),(5,5,'louver_angle','string',1,'\"mid\"','[\"up\", \"mid\", \"down\", \"swing\"]',NULL,NULL,'에어컨 바람 방향. up, mid, down, swing 중 하나.'),(6,6,'delay_minutes','integer',1,NULL,NULL,1,720,'예약 실행 또는 예약 종료까지의 지연 시간. 분 단위.'),(7,7,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'조명 전원 상태. on 또는 off.'),(8,8,'brightness','integer',1,NULL,NULL,0,100,'조명 밝기. 0에서 100 사이의 퍼센트 값.'),(9,9,'color','string',1,NULL,'[\"white\", \"yellow\", \"blue\", \"red\", \"green\"]',NULL,NULL,'조명 색상. white, yellow, blue, red, green 중 하나.'),(10,10,'color_temperature','integer',1,NULL,NULL,2700,6500,'조명 색온도. 2700K에서 6500K 사이.'),(11,11,'scene_name','string',1,NULL,'[\"sleep\", \"focus\", \"movie\", \"relax\"]',NULL,NULL,'조명 장면 모드. sleep, focus, movie, relax 중 하나.'),(28,12,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'TV 전원 상태. on 또는 off.'),(29,13,'volume','integer',1,NULL,NULL,0,100,'TV 볼륨. 0에서 100 사이의 정수.'),(30,14,'channel','integer',1,NULL,NULL,1,999,'TV 채널 번호. 1에서 999 사이의 정수.'),(31,15,'app_name','string',1,NULL,'[\"netflix\", \"youtube\", \"tving\", \"wavve\", \"disneyplus\", \"coupangplay\", \"browser\"]',NULL,NULL,'실행할 TV 앱 이름.'),(32,16,'content_title','string',1,NULL,NULL,NULL,NULL,'재생할 콘텐츠 제목. 사용자가 말한 제목을 그대로 사용한다. 예: 나는솔로, 뉴스, 축구 중계.'),(33,16,'app_name','string',0,'\"netflix\"','[\"netflix\", \"youtube\", \"tving\", \"wavve\", \"disneyplus\", \"coupangplay\"]',NULL,NULL,'콘텐츠를 재생할 앱 이름. 명시되지 않으면 기본값은 netflix.'),(53,16,'season','integer',0,NULL,NULL,1,99,'시리즈 콘텐츠의 시즌 번호. 단편 영화나 채널에는 불필요.'),(54,16,'episode','integer',0,NULL,NULL,1,9999,'시리즈 콘텐츠의 에피소드 번호. 단편 영화나 채널에는 불필요.');
    /*!40000 ALTER TABLE `command_parameters` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `device_states`
    --

    LOCK TABLES `device_states` WRITE;
    /*!40000 ALTER TABLE `device_states` DISABLE KEYS */;
    INSERT INTO `device_states` VALUES (1,1,'{\"mode\": \"cool\", \"power\": \"on\", \"fan_speed\": \"auto\", \"temperature\": 24, \"louver_angle\": \"mid\"}','2026-05-20 16:53:29'),(2,2,'{\"color\": \"white\", \"power\": \"off\", \"brightness\": 70, \"scene_name\": \"relax\", \"color_temperature\": 4000}','2026-05-06 07:08:00'),(3,3,'{\"power\": \"on\", \"volume\": 20, \"channel\": 1, \"app_name\": null, \"content_title\": \"나는솔로\"}','2026-05-21 06:36:57');
    /*!40000 ALTER TABLE `device_states` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `routines`
    --

    LOCK TABLES `routines` WRITE;
    /*!40000 ALTER TABLE `routines` DISABLE KEYS */;
    INSERT INTO `routines` VALUES (1,'sleep','수면 모드','취침을 위해 조명을 끄고 에어컨을 저소음 상태로 설정한다.',1,'2026-05-06 08:01:38','2026-05-06 08:01:38'),(2,'away','외출 모드','외출 시 조명과 에어컨을 모두 끈다.',1,'2026-05-06 08:01:38','2026-05-06 08:01:38'),(3,'movie','영화 모드','영화 감상에 맞게 TV를 켜고 Netflix를 실행하며 조명과 에어컨을 조정한다.',1,'2026-05-06 08:01:38','2026-05-20 08:09:23');
    /*!40000 ALTER TABLE `routines` ENABLE KEYS */;
    UNLOCK TABLES;

    --
    -- Dumping data for table `routine_steps`
    --

    LOCK TABLES `routine_steps` WRITE;
    /*!40000 ALTER TABLE `routine_steps` DISABLE KEYS */;
    INSERT INTO `routine_steps` VALUES (1,1,1,2,7,'{\"power\": \"off\"}',0,1,'2026-05-06 08:01:55'),(2,1,2,1,1,'{\"power\": \"on\"}',0,1,'2026-05-06 08:01:55'),(3,1,3,1,3,'{\"mode\": \"cool\"}',0,1,'2026-05-06 08:01:55'),(4,1,4,1,2,'{\"temperature\": 26}',0,1,'2026-05-06 08:01:55'),(5,1,5,1,4,'{\"fan_speed\": \"low\"}',0,1,'2026-05-06 08:01:55'),(6,2,1,2,7,'{\"power\": \"off\"}',0,1,'2026-05-06 08:01:59'),(7,2,2,1,1,'{\"power\": \"off\"}',0,1,'2026-05-06 08:01:59'),(14,3,1,3,12,'{\"power\": \"on\"}',0,1,'2026-05-20 08:09:23'),(15,3,2,3,15,'{\"app_name\": \"netflix\"}',1,1,'2026-05-20 08:09:23'),(16,3,3,2,7,'{\"power\": \"on\"}',0,1,'2026-05-20 08:09:23'),(17,3,4,2,8,'{\"brightness\": 30}',0,1,'2026-05-20 08:09:23'),(18,3,5,2,9,'{\"color\": \"yellow\"}',0,1,'2026-05-20 08:09:23'),(19,3,6,1,1,'{\"power\": \"on\"}',0,1,'2026-05-20 08:09:23'),(20,3,7,1,2,'{\"temperature\": 24}',0,1,'2026-05-20 08:09:23'),(21,3,8,1,4,'{\"fan_speed\": \"low\"}',0,1,'2026-05-20 08:09:23');
    /*!40000 ALTER TABLE `routine_steps` ENABLE KEYS */;
    UNLOCK TABLES;
    /*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

    /*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
    /*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
    /*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
    /*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
    /*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
    /*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
    /*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

    -- Dump completed on 2026-05-21 15:43:04






    --
    -- Dumping data for oven (Added manually)
    --

    LOCK TABLES `device_types` WRITE;
    /*!40000 ALTER TABLE `device_types` DISABLE KEYS */;
    INSERT INTO `device_types` VALUES (4,'oven','오븐','전원, 조리 모드, 온도, 팬 속도, 심부 온도를 제어하는 스마트 오븐',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `device_types` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `devices` WRITE;
    /*!40000 ALTER TABLE `devices` DISABLE KEYS */;
    INSERT INTO `devices` VALUES (4,4,'kitchen_oven','주방 오븐','kitchen',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `devices` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `device_states` WRITE;
    /*!40000 ALTER TABLE `device_states` DISABLE KEYS */;
    INSERT INTO `device_states` VALUES (4,4,'{\"power\": \"off\", \"mode\": \"bake\", \"target_temp\": 180, \"current_temp\": 25, \"timer_remaining\": 0, \"fan_speed\": \"off\", \"steam\": \"off\", \"probe_temp\": 25, \"light\": \"off\", \"door\": \"closed\"}',CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `device_states` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `commands` WRITE;
    /*!40000 ALTER TABLE `commands` DISABLE KEYS */;
    INSERT INTO `commands` VALUES 
    (17,4,'set_power','oven.set_power','오븐 전원 제어','오븐의 전원을 켜거나 끕니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (18,4,'set_temperature','oven.set_temperature','오븐 온도 설정','오븐의 목표 조리 온도를 정밀 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (19,4,'set_mode','oven.set_mode','오븐 조리 모드 설정','Bake, Convection Roast, Proof, AirFry, Dehydrate 등의 모드를 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (20,4,'set_fan_speed','oven.set_fan_speed','오븐 팬 속도 제어','컨벡션 팬 속도(Off, Low, High)를 조절합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (21,4,'set_steam','oven.set_steam','오븐 스팀 제어','조리 시 내부 습도 및 스팀 분사 상태를 조절합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (22,4,'set_probe_target','oven.set_probe_target','오븐 심부 온도 설정','고기 내부 목표 온도를 감지하여 요리를 자동 종료하도록 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `commands` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `command_parameters` WRITE;
    /*!40000 ALTER TABLE `command_parameters` DISABLE KEYS */;
    INSERT INTO `command_parameters` VALUES 
    (34,17,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'오븐 전원 상태 선택'),
    (35,18,'target_temp','integer',1,NULL,NULL,30,250,'오븐 설정 목표 온도'),
    (36,19,'mode','string',1,NULL,'[\"bake\", \"convection_roast\", \"proof\", \"air_fry\", \"dehydrate\"]',NULL,NULL,'원하는 조리 모드 선택'),
    (37,20,'fan_speed','string',1,'\"off\"','[\"off\", \"low\", \"high\"]',NULL,NULL,'컨벡션 팬 속도 단계'),
    (38,21,'steam','string',1,'\"off\"','[\"on\", \"off\"]',NULL,NULL,'내부 스팀 분기 가동 여부'),
    (39,22,'probe_target','integer',1,NULL,NULL,30,99,'심부 온도계 목표 도달 온도');
    /*!40000 ALTER TABLE `command_parameters` ENABLE KEYS */;
    UNLOCK TABLES;


    --
    -- Dumping data for air_purifier (Added manually)
    --

    LOCK TABLES `device_types` WRITE;
    /*!40000 ALTER TABLE `device_types` DISABLE KEYS */;
    INSERT INTO `device_types` VALUES (5,'air_purifier','공기청정기','전원, 모드, 풍량을 제어하고 실내 공기질을 관리하는 스마트 공기청정기',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `device_types` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `devices` WRITE;
    /*!40000 ALTER TABLE `devices` DISABLE KEYS */;
    INSERT INTO `devices` VALUES (5,5,'living_room_air_purifier','거실 공기청정기','living_room',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `devices` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `device_states` WRITE;
    /*!40000 ALTER TABLE `device_states` DISABLE KEYS */;
    -- 초기 상태: 전원 꺼짐, 자동 모드, 미세먼지 15(좋음)
    INSERT INTO `device_states` VALUES (5,5,'{\"power\": \"off\", \"mode\": \"auto\", \"fan_speed\": \"low\", \"air_quality\": \"good\", \"pm25\": 15, \"filter_status\": \"clean\"}',CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `device_states` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `commands` WRITE;
    /*!40000 ALTER TABLE `commands` DISABLE KEYS */;
    INSERT INTO `commands` VALUES 
    (23,5,'set_power','air_purifier.set_power','공기청정기 전원 제어','공기청정기의 전원을 켜거나 끕니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (24,5,'set_mode','air_purifier.set_mode','공기청정기 모드 설정','Auto, Manual, Sleep 등의 운전 모드를 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
    (25,5,'set_fan_speed','air_purifier.set_fan_speed','공기청정기 풍량 제어','풍량(Low, Medium, High)을 조절합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
    /*!40000 ALTER TABLE `commands` ENABLE KEYS */;
    UNLOCK TABLES;


    LOCK TABLES `command_parameters` WRITE;
    /*!40000 ALTER TABLE `command_parameters` DISABLE KEYS */;
    INSERT INTO `command_parameters` VALUES 
    (40,23,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'공기청정기 전원 상태 선택'),
    (41,24,'mode','string',1,NULL,'[\"auto\", \"manual\", \"sleep\"]',NULL,NULL,'공기청정기 운전 모드 선택'),
    (42,25,'fan_speed','string',1,'\"low\"','[\"low\", \"medium\", \"high\"]',NULL,NULL,'공기청정기 풍량 단계');
    /*!40000 ALTER TABLE `command_parameters` ENABLE KEYS */;
    UNLOCK TABLES;





    --
-- Dumping data for washing_machine (Added manually)
--

LOCK TABLES `device_types` WRITE;
/*!40000 ALTER TABLE `device_types` DISABLE KEYS */;
INSERT INTO `device_types` VALUES (6,'washing_machine','세탁기','전원, 세탁 모드, 탈수 강도, 물 온도, 예약을 제어하는 스마트 세탁기',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `device_types` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `devices` WRITE;
/*!40000 ALTER TABLE `devices` DISABLE KEYS */;
INSERT INTO `devices` VALUES (6,6,'utility_room_washing_machine','다용도실 세탁기','utility_room',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `devices` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `device_states` WRITE;
/*!40000 ALTER TABLE `device_states` DISABLE KEYS */;
-- 초기 상태: 전원 꺼짐, 정지(stopped) 상태, 도어 닫힘(closed), 표준 모드
INSERT INTO `device_states` VALUES (6,6,'{\"power\": \"off\", \"mode\": \"standard\", \"status\": \"stopped\", \"remaining_time\": 0, \"spin_speed\": \"medium\", \"door\": \"closed\", \"water_temperature\": 30, \"reservation_time\": null, \"error\": null}',CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `device_states` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `commands` WRITE;
/*!40000 ALTER TABLE `commands` DISABLE KEYS */;
INSERT INTO `commands` VALUES 
(26,6,'set_power','washing_machine.set_power','세탁기 전원 제어','세탁기의 전원을 켜거나 끕니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(27,6,'set_action','washing_machine.set_action','세탁기 동작 제어','세탁 시작, 정지, 일시정지, 재개를 수행합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(28,6,'set_mode','washing_machine.set_mode','세탁기 모드 설정','표준, 울, 급속 등 다양한 세탁 모드를 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(29,6,'set_spin_speed','washing_machine.set_spin_speed','세탁기 탈수 강도 설정','탈수 강도(Low, Medium, High)를 조절합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(30,6,'set_water_temperature','washing_machine.set_water_temperature','세탁기 물 온도 설정','세탁 시 사용할 물의 온도를 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(31,6,'set_reservation','washing_machine.set_reservation','세탁기 예약 설정','지정한 시간에 세탁이 시작되도록 예약합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `commands` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `command_parameters` WRITE;
/*!40000 ALTER TABLE `command_parameters` DISABLE KEYS */;
INSERT INTO `command_parameters` VALUES 
(43,26,'power','string',1,NULL,'[\"on\", \"off\"]',NULL,NULL,'세탁기 전원 상태 선택'),
(44,27,'action','string',1,NULL,'[\"start\", \"stop\", \"pause\", \"resume\"]',NULL,NULL,'세탁기 동작 상태(시작/정지/일시정지/재개)'),
(45,28,'mode','string',1,NULL,'[\"standard\", \"heavy\", \"baby\", \"silent\", \"color\", \"boil\", \"sport\", \"delicate\", \"bedding\", \"quick\", \"rinse\", \"wool\"]',NULL,NULL,'원하는 세탁 코스 선택'),
(46,29,'spin_speed','string',1,'\"medium\"','[\"low\", \"medium\", \"high\"]',NULL,NULL,'탈수 강도 단계'),
(47,30,'water_temperature','integer',1,NULL,NULL,0,95,'세탁 물 온도 설정 (도 단위)'),
(48,31,'start_time','string',1,NULL,NULL,NULL,NULL,'예약 시작 시간 (예: \"20:00\" 또는 시간 포맷)');
/*!40000 ALTER TABLE `command_parameters` ENABLE KEYS */;
UNLOCK TABLES;



--
-- Dumping data for robot_vacuum (Added manually)
--

LOCK TABLES `device_types` WRITE;
/*!40000 ALTER TABLE `device_types` DISABLE KEYS */;
INSERT INTO `device_types` VALUES (7,'robot_vacuum','로봇청소기','동작 상태, 구역 지정, 흡입 강도, 청소 패턴을 제어하는 스마트 로봇청소기',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `device_types` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `devices` WRITE;
/*!40000 ALTER TABLE `devices` DISABLE KEYS */;
INSERT INTO `devices` VALUES (7,7,'living_room_robot_vacuum','거실 로봇청소기','living_room',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `devices` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `device_states` WRITE;
/*!40000 ALTER TABLE `device_states` DISABLE KEYS */;
-- 초기 상태: 도킹 중, 배터리 100%, 구역 없음, 방해금지 꺼짐
INSERT INTO `device_states` VALUES (7,7,'{\"status\": \"docked\", \"battery_pct\": 100, \"zone\": null, \"suction_power\": \"standard\", \"cleaning_mode\": \"auto\", \"cleaned_area_m2\": 0.0, \"position\": {\"x\": 0.0, \"y\": 0.0}, \"do_not_disturb\": false, \"error\": null}',CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `device_states` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `commands` WRITE;
/*!40000 ALTER TABLE `commands` DISABLE KEYS */;
INSERT INTO `commands` VALUES 
(32,7,'set_action','robot_vacuum.set_action','로봇청소기 동작 제어','청소 시작, 일시정지, 재개, 충전기 귀환 명령을 수행합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(33,7,'set_zone','robot_vacuum.set_zone','로봇청소기 구역 지정','특정 방이나 구역을 배열 형태로 지정하여 청소합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(34,7,'set_suction_power','robot_vacuum.set_suction_power','로봇청소기 흡입 강도 설정','흡입 강도(quiet, standard, strong, max)를 조절합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(35,7,'set_cleaning_mode','robot_vacuum.set_cleaning_mode','로봇청소기 청소 패턴 설정','자동, 지그재그, 스팟, 엣지 등 청소 패턴을 설정합니다.',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `commands` ENABLE KEYS */;
UNLOCK TABLES;


LOCK TABLES `command_parameters` WRITE;
/*!40000 ALTER TABLE `command_parameters` DISABLE KEYS */;
INSERT INTO `command_parameters` VALUES 
(49,32,'action','string',1,NULL,'[\"start_cleaning\", \"pause\", \"resume\", \"return_to_dock\"]',NULL,NULL,'로봇청소기 동작 상태 제어'),
(50,33,'zone','string',0,NULL,NULL,NULL,NULL,'청소할 구역 지정 (예: \"living_room\")'),
(51,34,'suction_power','string',1,'\"standard\"','[\"quiet\", \"standard\", \"strong\", \"max\"]',NULL,NULL,'흡입 강도 단계'),
(52,35,'cleaning_mode','string',1,'\"auto\"','[\"auto\", \"zigzag\", \"spot\", \"edge\"]',NULL,NULL,'청소 이동 패턴');
/*!40000 ALTER TABLE `command_parameters` ENABLE KEYS */;
UNLOCK TABLES;
    







