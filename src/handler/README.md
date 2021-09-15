# doc

## query code

to solve callback queries conflicts, each query has a form like `<handler-code><data>`:

* `<handler-code>` is a numeric code with 4 digits in base 10 (`[0-9][0-9][0-9][0-9]`). the first 2 digits are the type code and the last 2 digits are the handler code (in its type). it is also for `context.user_data`, in form `<handler-code><key>`. here is the list of the codes:

| name                | code |
|---------------------|------|
| add_new_command     | 0000 |
| add_new_group       | 0001 |
| add_special_command | 0002 |
| add_filter (BUG)    | 0003 |
| get_command         | 0100 |
| get_special         | 0101 |
| watch               | 0102 |
| get_filter          | 0103 |
| del_command         | 0200 |
| del_special         | 0201 |
| del_group           | 0202 |
| del_filter          | 0203 |
| backup              | 0300 |
| database            | 0301 |
| export              | 0400 |
| set_locks           | 0500 |
| start_command       | 0600 |

* `<data>` contains the data, which is used by handler.
