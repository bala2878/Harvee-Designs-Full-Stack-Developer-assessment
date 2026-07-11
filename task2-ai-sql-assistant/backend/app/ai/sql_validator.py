import sqlglot
from sqlglot import exp

from app.core.config import settings
_DENYLISTED_FUNCTIONS = {
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_sleep",
    "pg_sleep_for",
    "lo_import",
    "lo_export",
    "dblink",
    "dblink_connect",
    "current_setting",
    "set_config",
}

_DISALLOWED_STATEMENT_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Grant,
    exp.TruncateTable,
    exp.Command,
)


class SQLValidationError(Exception):
    pass


def validate_and_prepare(raw_sql: str, allowed_table: str) -> str:

    raw_sql = raw_sql.strip().rstrip(";")

    if not raw_sql:
        raise SQLValidationError("Generated SQL was empty.")

    try:
        statements = sqlglot.parse(raw_sql, read="postgres")
    except Exception as e:
        raise SQLValidationError(f"Generated SQL failed to parse: {e}") from e

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise SQLValidationError("Only a single SQL statement is allowed (no statement stacking).")

    stmt = statements[0]

    if isinstance(stmt, _DISALLOWED_STATEMENT_TYPES):
        raise SQLValidationError("Only SELECT queries are allowed.")

    if not isinstance(stmt, (exp.Select, exp.Union)) and not _is_cte_select(stmt):
        raise SQLValidationError("Only SELECT (optionally with CTEs) queries are allowed.")

    cte_aliases = set()
    for with_node in stmt.find_all(exp.With):
        for cte in with_node.find_all(exp.CTE):
            alias = cte.alias_or_name
            if alias:
                cte_aliases.add(alias.lower())

    referenced_tables = set()
    for table in stmt.find_all(exp.Table):
        qualified = ".".join(part for part in (table.db, table.name) if part)
        referenced_tables.add(qualified.lower())
        referenced_tables.add(table.name.lower())  # also allow unqualified match
    referenced_tables -= cte_aliases

    allowed_variants = {allowed_table.lower(), allowed_table.split(".")[-1].lower()}
    if not referenced_tables.issubset(allowed_variants):
        offending = referenced_tables - allowed_variants
        raise SQLValidationError(
            f"Query references table(s) outside the allowed dataset: {', '.join(offending)}"
        )
    if not referenced_tables and not cte_aliases:
        raise SQLValidationError("Query does not reference the dataset table at all.")

    for func in stmt.find_all(exp.Anonymous, exp.Func):
        fname = (getattr(func, "name", "") or "").lower()
        if fname in _DENYLISTED_FUNCTIONS:
            raise SQLValidationError(f"Function '{fname}' is not permitted in generated queries.")

    if isinstance(stmt, exp.Union):
        _apply_limit(stmt)
    else:
        target = stmt if isinstance(stmt, exp.Select) else None
        if target is not None:
            _apply_limit(target)

    return stmt.sql(dialect="postgres")


def _apply_limit(node: exp.Select | exp.Union) -> None:
    existing_limit = node.args.get("limit")
    if existing_limit is not None:
        try:
            limit_value = int(existing_limit.expression.this)
        except (ValueError, AttributeError, TypeError):
            limit_value = None
        if limit_value is None or limit_value > settings.MAX_RESULT_ROWS:
            node.set("limit", exp.Limit(expression=exp.Literal.number(settings.MAX_RESULT_ROWS)))
    else:
        node.set("limit", exp.Limit(expression=exp.Literal.number(settings.MAX_RESULT_ROWS)))


def _is_cte_select(stmt: exp.Expression) -> bool:
    return isinstance(stmt, exp.Select) and any(stmt.find_all(exp.With))
