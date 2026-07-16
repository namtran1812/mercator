ALTER TABLE rfqs
ADD COLUMN IF NOT EXISTS account_id UUID;

ALTER TABLE executions
ADD COLUMN IF NOT EXISTS account_id UUID;

UPDATE rfqs
SET account_id =
    '00000000-0000-0000-0000-000000000101'
WHERE account_id IS NULL;

UPDATE executions
SET account_id =
    '00000000-0000-0000-0000-000000000101'
WHERE account_id IS NULL;

ALTER TABLE rfqs
ALTER COLUMN account_id SET NOT NULL;

ALTER TABLE executions
ALTER COLUMN account_id SET NOT NULL;

ALTER TABLE rfqs
ADD CONSTRAINT rfqs_account_fk
FOREIGN KEY (account_id)
REFERENCES trading_accounts(account_id);

ALTER TABLE executions
ADD CONSTRAINT executions_account_fk
FOREIGN KEY (account_id)
REFERENCES trading_accounts(account_id);
