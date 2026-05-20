\# smart\_home\_aiot Database



자연어 기반 스마트홈 AIoT 제어 시스템의 MySQL DB 스키마 및 초기 데이터입니다.



이 폴더는 팀원들이 동일한 DB 구조를 각자 로컬 MySQL 환경에 재현할 수 있도록 하기 위한 SQL 파일들을 포함합니다.



\---



\## 1. 구성 파일



| 파일 | 설명 |

|---|---|

| `schema.sql` | 테이블 구조 생성 SQL |

| `seed.sql` | 초기 데이터 삽입 SQL |

| `smart\_home\_aiot\_full.sql` | 테이블 구조 + 초기 데이터 전체 백업 |

| `sample\_queries.sql` | DB 적용 후 확인용 쿼리 |

| `README.md` | DB 사용 방법 안내 문서 |



\---



\## 2. 현재 테이블 구성



현재 DB는 총 9개 테이블로 구성됩니다.



| 테이블 | 역할 |

|---|---|

| `device\_types` | 기기 종류 정의 |

| `devices` | 실제 기기 인스턴스 정의 |

| `commands` | 기기별 실행 가능한 명령 정의 |

| `command\_parameters` | 명령별 파라미터 규격 정의 |

| `device\_states` | 현재 기기 상태 저장 |

| `dialogue\_sessions` | 대화 세션 및 재질문 상태 저장 |

| `command\_logs` | 명령 실행 로그 저장 |

| `routines` | 수면 모드, 영화 모드 등 루틴 정의 |

| `routine\_steps` | 루틴별 실행 단계 정의 |



\---



\## 3. DB 생성



먼저 MySQL에 접속합니다.



```bash

mysql -u root -p

```



MySQL에 접속한 뒤 아래 SQL을 실행합니다.



```sql

CREATE DATABASE smart\_home\_aiot

CHARACTER SET utf8mb4

COLLATE utf8mb4\_unicode\_ci;



EXIT;

```



\---



\## 4. schema.sql 적용



프로젝트 루트 폴더에서 아래 명령어를 실행합니다.



```bash

mysql -u root -p smart\_home\_aiot < database/schema.sql

```



\---



\## 5. seed.sql 적용



schema 적용 후 초기 데이터를 삽입합니다.



```bash

mysql -u root -p smart\_home\_aiot < database/seed.sql

```



\---



\## 6. 전체 백업 파일로 한 번에 복원하는 방법



`schema.sql`과 `seed.sql`을 따로 적용하지 않고, 전체 백업 파일을 사용할 수도 있습니다.



```bash

mysql -u root -p smart\_home\_aiot < database/smart\_home\_aiot\_full.sql

```



주의: `smart\_home\_aiot\_full.sql`을 사용할 경우 `schema.sql`, `seed.sql`을 따로 적용하지 않아도 됩니다.



\---



\## 7. 적용 확인



DB 적용 후 아래 명령어로 확인용 쿼리를 실행합니다.



```bash

mysql -u root -p smart\_home\_aiot < database/sample\_queries.sql

```



또는 MySQL에 직접 접속해서 확인할 수 있습니다.



```bash

mysql -u root -p

```



```sql

USE smart\_home\_aiot;



SHOW TABLES;

```



\---



\## 8. 주요 데이터 확인 쿼리



\### 8.1 테이블 개수 확인



```sql

SELECT COUNT(\*) AS table\_count

FROM information\_schema.tables

WHERE table\_schema = 'smart\_home\_aiot';

```



기대 결과는 9입니다.



\---



\### 8.2 주요 테이블 데이터 개수 확인



```sql

SELECT 'device\_types' AS table\_name, COUNT(\*) AS count FROM device\_types

UNION ALL

SELECT 'devices', COUNT(\*) FROM devices

UNION ALL

SELECT 'commands', COUNT(\*) FROM commands

UNION ALL

SELECT 'command\_parameters', COUNT(\*) FROM command\_parameters

UNION ALL

SELECT 'device\_states', COUNT(\*) FROM device\_states

UNION ALL

SELECT 'routines', COUNT(\*) FROM routines

UNION ALL

SELECT 'routine\_steps', COUNT(\*) FROM routine\_steps;

```



\---



\### 8.3 명령 목록 확인



```sql

SELECT

&#x20;   dt.name AS device\_type,

&#x20;   c.action\_name,

&#x20;   c.tool\_name,

&#x20;   c.display\_name

FROM commands c

JOIN device\_types dt ON c.device\_type\_id = dt.id

ORDER BY dt.name, c.id;

```



\---



\### 8.4 명령 파라미터 확인



```sql

SELECT

&#x20;   dt.name AS device\_type,

&#x20;   c.tool\_name,

&#x20;   cp.param\_name,

&#x20;   cp.param\_type,

&#x20;   cp.is\_required,

&#x20;   cp.default\_value,

&#x20;   cp.allowed\_values,

&#x20;   cp.min\_value,

&#x20;   cp.max\_value

FROM command\_parameters cp

JOIN commands c ON cp.command\_id = c.id

JOIN device\_types dt ON c.device\_type\_id = dt.id

ORDER BY dt.name, c.id, cp.id;

```



\---



\### 8.5 기기 상태 확인



```sql

SELECT

&#x20;   d.name AS device\_name,

&#x20;   d.display\_name,

&#x20;   d.location,

&#x20;   JSON\_PRETTY(ds.state\_data) AS state\_data

FROM device\_states ds

JOIN devices d ON ds.device\_id = d.id

ORDER BY d.name;

```



\---



\### 8.6 루틴 상세 확인



```sql

SELECT

&#x20;   r.name AS routine\_name,

&#x20;   r.display\_name AS routine\_display\_name,

&#x20;   rs.step\_order,

&#x20;   d.name AS device\_name,

&#x20;   c.tool\_name,

&#x20;   JSON\_PRETTY(rs.input\_params) AS input\_params,

&#x20;   rs.delay\_seconds

FROM routine\_steps rs

JOIN routines r ON rs.routine\_id = r.id

JOIN devices d ON rs.device\_id = d.id

JOIN commands c ON rs.command\_id = c.id

ORDER BY r.name, rs.step\_order;

```



\---



\## 9. 현재 지원 기기



현재 1차 MVP 기준 지원 기기는 다음과 같습니다.



| device\_type | 설명 |

|---|---|

| `air\_conditioner` | 에어컨 |

| `light` | 조명 |

| `tv` | TV |



\---



\## 10. 현재 주요 명령



\### 10.1 에어컨 명령



| tool\_name | 설명 |

|---|---|

| `air\_conditioner.set\_power` | 에어컨 전원 제어 |

| `air\_conditioner.set\_temperature` | 에어컨 온도 설정 |

| `air\_conditioner.set\_mode` | 에어컨 운전 모드 설정 |

| `air\_conditioner.set\_fan\_speed` | 에어컨 풍량 설정 |

| `air\_conditioner.set\_louver\_angle` | 에어컨 바람 방향 설정 |

| `air\_conditioner.set\_timer` | 에어컨 예약 설정 |



\---



\### 10.2 조명 명령



| tool\_name | 설명 |

|---|---|

| `light.set\_power` | 조명 전원 제어 |

| `light.set\_brightness` | 조명 밝기 설정 |

| `light.set\_color` | 조명 색상 설정 |

| `light.set\_color\_temperature` | 조명 색온도 설정 |

| `light.set\_scene` | 조명 장면 모드 설정 |



\---



\### 10.3 TV 명령



| tool\_name | 설명 |

|---|---|

| `tv.set\_power` | TV 전원 제어 |

| `tv.set\_volume` | TV 볼륨 설정 |

| `tv.set\_channel` | TV 채널 설정 |

| `tv.open\_app` | TV 앱 실행 |

| `tv.play\_content` | TV 콘텐츠 재생 |



`tv.play\_content`의 `content\_title`은 자유 입력 방식입니다.  

예를 들어 사용자가 "나는솔로 틀어줘"라고 말하면 `content\_title`에 `"나는솔로"`가 그대로 들어갑니다.



\---



\## 11. 주요 설계 원칙



1\. DB는 기기별 명령 사전 역할을 합니다.

2\. `commands`와 `command\_parameters`는 MCP Tool schema 생성 기준입니다.

3\. `device\_states`는 현재 기기 상태를 JSON으로 저장합니다.

4\. `routines`와 `routine\_steps`는 수면 모드, 영화 모드, 외출 모드 같은 복합 루틴을 저장합니다.

5\. AI/MCP Server는 DB에 직접 접근하지 않고 Backend API를 통해 Tool/Resource 정보를 가져옵니다.

6\. Backend는 AI/MCP Server가 생성한 명령을 최종 검증하고 실행합니다.

7\. Frontend는 Backend가 전달한 표준 상태 JSON을 기준으로 시뮬레이터 상태를 갱신합니다.



\---



\## 12. 팀원 사용 흐름



팀원이 처음 DB를 세팅할 때는 아래 순서로 진행합니다.



```bash

git pull

mysql -u root -p

```



```sql

CREATE DATABASE smart\_home\_aiot

CHARACTER SET utf8mb4

COLLATE utf8mb4\_unicode\_ci;



EXIT;

```



```bash

mysql -u root -p smart\_home\_aiot < database/schema.sql

mysql -u root -p smart\_home\_aiot < database/seed.sql

mysql -u root -p smart\_home\_aiot < database/sample\_queries.sql

```



\---



\## 13. 주의사항



\- `.env` 파일, DB 비밀번호, API Key는 GitHub에 올리지 않습니다.

\- 실제 사용자 대화 로그나 개인정보가 쌓인 DB dump는 공유하지 않습니다.

\- DB 구조 변경이 필요한 경우 `schema.sql` 또는 `seed.sql`을 수정한 뒤 GitHub에 반영합니다.

\- 팀원들은 최신 변경사항을 받기 위해 `git pull` 후 DB를 다시 적용합니다.

