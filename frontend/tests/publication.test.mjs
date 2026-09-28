import assert from 'node:assert/strict';
import test from 'node:test';
import {build} from 'esbuild';
const output = await build({entryPoints:['config/publication.ts'],bundle:true,write:false,format:'esm',platform:'node'});
const {publicationReady,validatePublication} = await import('data:text/javascript;base64,'+Buffer.from(output.outputFiles[0].text).toString('base64'));

const approved = {
  APP_ENV:'production', SALES_PUBLICATION_APPROVED:'true', LEGAL_REVIEW_APPROVED:'true',
  COMMERCIAL_DISCLOSURE_APPROVED:'true', SELLER_NAME:'販売者名', SELLER_ADDRESS:'東京都の確定住所',
  SUPPORT_EMAIL:'support@profit-radar.jp', SUPPORT_PHONE:'03-0000-0000',
  REFUND_POLICY:'返金条件の確定文', CANCELLATION_POLICY:'期間末解約の確定文',
  PRIVACY_CONTACT:'privacy@profit-radar.jp', INTERNATIONAL_TRANSFER_DISCLOSURE:'外部委託先と移転条件の確定文',
  DATA_DELETION_POLICY:'解約後の削除条件の確定文', GOVERNING_COURT:'東京地方裁判所',
  TERMS_EFFECTIVE_DATE:'2026-10-01',
  DATA_RETENTION_DAYS:'365', BACKUP_RETENTION_DAYS:'30'
};

test('approved complete publication configuration passes',()=>{
  assert.equal(publicationReady(approved),true);
  assert.doesNotThrow(()=>validatePublication(approved));
});
test('production rejects missing, placeholder and unapproved publication data',()=>{
  for(const change of [
    {SELLER_NAME:''},{SELLER_ADDRESS:'TODO'},{SUPPORT_EMAIL:'owner@example.com'},
    {DATA_RETENTION_DAYS:'0'},{LEGAL_REVIEW_APPROVED:'false'}
  ]) assert.throws(()=>validatePublication({...approved,...change}),/incomplete/);
});
test('non-production build may render the explicit preparation state',()=>{
  assert.doesNotThrow(()=>validatePublication({APP_ENV:'test'}));
  assert.equal(publicationReady({APP_ENV:'test'}),false);
});
