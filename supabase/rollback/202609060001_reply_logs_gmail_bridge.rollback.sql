-- Intentionally non-destructive. On an already-existing installation these
-- columns predate migration tracking, so a post-COMMIT DROP cannot distinguish
-- legacy columns from columns first added by this bridge. A failed application
-- is transactionally rolled back; a committed release must use backup restore
-- or a reviewed forward fix rather than risk deleting Gmail identity data.
begin;
do $$ begin
  raise exception 'BRIDGE ROLLBACK: destructive column removal is not permitted';
end $$;
rollback;
