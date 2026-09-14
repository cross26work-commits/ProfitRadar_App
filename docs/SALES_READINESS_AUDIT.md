# Profit Radar 蛻晄悄3遉ｾ雋ｩ螢ｲ貅門ｙ逶｣譟ｻ

> 2026-09-10縺ｮ譛譁ｰ蜀咲屮譟ｻ縺ｯ [PRE_SALES_AUDIT_20260910.md](PRE_SALES_AUDIT_20260910.md)縲よ悴繧ｳ繝溘ャ繝亥ｷｮ蛻・・讀懆ｨｼdigest縲・4 passed/15 skipped縲・8鬆伜沺縺ｨP0/P1繧定ｨ倬鹸縲ゆｻ･荳九・2026-09-09縺ｾ縺ｧ縺ｮ螻･豁ｴ縲・
逶｣譟ｻ譌･: 2026-09-08 JST
蟇ｾ雎｡: `arc/profit-radar-release-readiness` / `3c9a83ad2264899187bd67d1ec9ccac7b8100f70`
菴懈･ｭ繝・Μ繝ｼ: 譌｢蟄倥・霑ｽ霍｡貂医∩繝ｻ譛ｪ霑ｽ霍｡螟画峩縺ゅｊ縲ゆｻ雁屓縺ｮ逶｣譟ｻ縺ｧ縺ｯ遐ｴ譽・・螟夜Κ驕ｩ逕ｨ繝ｻ螳溘Γ繝ｼ繝ｫ騾∽ｿ｡繧偵＠縺ｦ縺・↑縺・・
譖ｴ譁ｰ: 2026-09-09 JST縲１0縲・∽ｿ｡ledger縲∬ｩｦ逕ｨ/test隱ｲ驥代∝酔譛毆orker縲∽ｿ晏ｭ連I陦ｨ遉ｺ縲∬ｲｩ螢ｲUI繧定ｿｽ蜉縲よ怙譁ｰ蟾ｮ蛻・・ `SALES_COMPLETION_CHECKPOINT_20260909.md`縲ょｮ欖upabase縺ｮ隱ｭ縺ｿ蜿悶ｊ逶｣譟ｻ縺ｯ縲∫腸蠅・ｨｮ蛻･縺ｨ謗･邯壽ュ蝣ｱ繧貞ｮ牙・縺ｫ遒ｺ隱阪〒縺阪↑縺・◆繧∵悴螳滓命縲・
## 邨占ｫ・
**蛻晄悄3遉ｾ縺ｸ縺ｮ譛画侭謠蝉ｾ帙・迴ｾ譎らせ縺ｧ縺ｯ荳榊庄縲・* UI繝ｻ蝙区､懈渊繝ｻ繝薙Ν繝峨・騾壹ｋ縺後；mail restricted scope縺ｮ螟夜Κ謠蝉ｾ帶擅莉ｶ縲√ヨ繝ｼ繧ｯ繝ｳ菫晁ｭｷ縲∫ｶ咏ｶ壼酔譛溘・∽ｿ｡邨先棡縺ｮ蜀ｪ遲画ｧ縲∬ｪｲ驥・隧ｦ逕ｨ縲ヽLS螳溽腸蠅・ｨｼ霍｡縲∝炎髯､/菫晄戟驕狗畑縺梧悴螳後∪縺溘・譛ｪ遒ｺ隱阪〒縺ゅｋ縲・
髫秘屬縺輔ｌ縺滓焔蜍墓髪謠ｴ荳九〒縲隈mail謗･邯壹↑縺励・騾∽ｿ｡縺ｪ縺励阪・逕ｻ髱｢隧穂ｾ｡縺ｯ蜿ｯ閭ｽ縺縺後∵怦鬘崎ｪｲ驥代・雋ｩ螢ｲ譚｡莉ｶ繧呈ｺ縺溘☆譬ｹ諡縺ｫ縺ｯ縺ｪ繧峨↑縺・・
## 螳溯｡後＠縺滓､懆ｨｼ

| 繧ｳ繝槭Φ繝・| 邨先棡 | 髯千阜 |
|---|---|---|
| `venv/Scripts/python.exe -m pytest -q`・・ackend縺ｧ螳溯｡鯉ｼ・| 83 passed / 15 skipped・・026-09-09邯咏ｶ壻ｽ懈･ｭ・・| 螳欖upabase/Auth繝・せ繝・5莉ｶ縺ｯ迺ｰ蠅・↑縺励〒skip縲・1莉ｶ縺ｯSQL grammar縺ｮ縺ｿ縲ょ､夜Κ騾∽ｿ｡縺ｪ縺・|
| `python -m compileall -q app` | 蜷域ｼ | 螳溯｡梧凾DB schema縺ｯ讀懆ｨｼ縺励↑縺・|
| `npx tsc --noEmit` | 蜷域ｼ | API/DB螳滄壻ｿ｡繧呈､懆ｨｼ縺励↑縺・|
| `npm run lint` | 蜷域ｼ | E2E縺ｧ縺ｯ縺ｪ縺・|
| `npm run build` | 蜷域ｼ縲・0 routes | auth/Gmail/DB縺ｮ螳溷虚菴懆ｨｼ諡縺ｧ縺ｯ縺ｪ縺・|
| `git diff --check` | 蜷域ｼ | 謾ｹ陦後さ繝ｼ繝芽ｭｦ蜻翫・縺ｿ |
| secret/mojibake髱咏噪讀懃ｴ｢ | source遐ｴ謳榊呵｣懊↑縺・| env蛟､繝ｻ螳櫂B蛻怜､縺ｯ讀懈渊縺励↑縺・|

迥ｶ諷九・縲悟粋譬ｼ=蠢・ｦ√↑螳溯｡梧､懆ｨｼ縺ｾ縺ｧ螳御ｺ・阪御ｸ榊粋譬ｼ=谺髯･/谺關ｽ遒ｺ隱阪阪梧悴遒ｺ隱・螳櫂B遲峨・蜍穂ｽ懆ｨｼ諡縺ｪ縺励阪悟ｯｾ雎｡螟・蛻晄悄雋ｩ螢ｲ遽・峇螟悶阪・4遞ｮ縺ｮ縺ｿ繧堤畑縺・ｋ縲る撕逧・・build蜷域ｼ縺ｯ螳櫂B/API蜷域ｼ縺ｨ蛹ｺ蛻･縺吶ｋ縲ゆｸ区嶌縺堺ｿ晏ｭ倥・繝ｦ繝ｼ繧ｶ繝ｼ縺悟ｮ溯｣・ｯｾ雎｡縺ｨ遒ｺ螳壽ｸ医∩縲・PI繝ｻUI繝ｻ譛ｪ驕ｩ逕ｨmigration繝ｻunit test繧定ｿｽ蜉縺励∝ｮ櫂B/E2E讀懆ｨｼ蠕・■縺ｧ縺ゅｋ縲・
逶｣譟ｻ陦ｨ縺ｮ迥ｶ諷倶ｻｶ謨ｰ: 蜷域ｼ 0 / 荳榊粋譬ｼ 14 / 譛ｪ遒ｺ隱・18 / 蟇ｾ雎｡螟・1・・3陦鯉ｼ峨ゅユ繧ｹ繝医さ繝槭Φ繝峨・蜷域ｼ莉ｶ謨ｰ縺ｯ縺薙・迥ｶ諷倶ｻｶ謨ｰ縺ｫ蜷ｫ繧√↑縺・・
## 逶｣譟ｻ陦ｨ

| ID | 鬆・岼 | 迥ｶ諷・| 險ｼ諡 | 蠖ｱ髻ｿ | 蠢・ｦ√↑菫ｮ豁｣ / 蜀肴､懆ｨｼ |
|---|---|---|---|---|---|
| A01 | Register/Login | 譛ｪ遒ｺ隱・| Supabase Auth UI/API縺ゅｊ | 螳溘そ繝・す繝ｧ繝ｳ縺ｪ縺・| 譁ｰ隕上Θ繝ｼ繧ｶ繝ｼ縺ｧAuth竊弛nboarding竊値ogout/login E2E |
| A02 | Onboarding | 譛ｪ遒ｺ隱・| `backend/app/api/onboarding.py` 縺ｯRPC蜻ｼ蜃ｺ | RPC螳夂ｾｩ/grant荳肴・ | 螳櫂B縺ｧfunction/search_path/EXECUTE逶｣譟ｻ |
| A03 | Gmail騾｣謳ｺ | 譛ｪ遒ｺ隱・| `gmail.py` OAuth URL/callback縺ゅｊ | provider險ｭ螳壻ｸ肴・ | test Google account縺ｧcallback遒ｺ隱・|
| A04 | 繝｡繝ｼ繝ｫ蜿門ｾ・蝠・ｫ・､懃衍 | 荳榊粋譬ｼ | scheduler worker/lock/run霑ｽ蜉縲∵里遏･event讀懃衍縺ｮ縺ｿ | 蛻晏屓蜈ｨ蜿門ｾ励・蟾ｮ蛻・ｾｩ譌ｧ譛ｪ螳・| pagination/cursor螳溯｣・ｾ後↓螳壽悄襍ｷ蜍髭2E |
| A05 | 譯井ｻｶ荳隕ｧ | 譛ｪ遒ｺ隱・| `/leads` UI/API縲｜uild騾夐℃ | 螳溘ョ繝ｼ繧ｿ譛ｪ遒ｺ隱・| tenant A/B API E2E |
| A06 | Customer Detail SSR | 譛ｪ遒ｺ隱・| server helper縺ｧ4 API | JWT/DB螳溯ｨｼ縺ｪ縺・| authenticated SSR E2E |
| A07 | 霑比ｿ｡譯郁｡ｨ遉ｺ/邱ｨ髮・| 譛ｪ遒ｺ隱・| `ReplyDraftForm` | OpenAI螳滓嫌蜍墓悴遒ｺ隱・| mock + test tenant E2E |
| A08 | 荳区嶌縺堺ｿ晏ｭ・| 譛ｪ遒ｺ隱・| 菫晏ｭ連PI/UI繝ｻ蠕ｩ蜈・・unit test霑ｽ蜉 | migration譛ｪ驕ｩ逕ｨ縲∝ｮ櫂B譛ｪ讀懆ｨｼ | 髫秘屬DB縺ｧ菫晏ｭ倪・reload竊貞・繝ｭ繧ｰ繧､繝ｳ縺ｨ莉也､ｾ諡貞凄 |
| A09 | Gmail騾∽ｿ｡遒ｺ隱・| 譛ｪ遒ｺ隱・| confirm dialog + backend recipient蜀崎ｧ｣豎ｺ | 螳殳hread/騾∽ｿ｡邨先棡譛ｪ遒ｺ隱・| mock thread test蠕後∫ｮ｡逅・ｸ季mail E2E |
| A10 | 霑比ｿ｡讀懃衍/邨先棡險倬鹸 | 荳榊粋譬ｼ | 隍・焚DB write縺碁撼transaction | partial state/驥崎､・| idempotency operation + recovery險ｭ險・|
| B01 | JWT/company蠅・阜 | 譛ｪ遒ｺ隱・| API縺ｮ螟壹￥縺ｯ`get_current_company_id`縲￣0 migration霑ｽ蜉 | 螳櫂B/RLS驕ｩ逕ｨ蜑・| A/B JWT縺ｧ荳隕ｧ縲∬ｩｳ邏ｰ縲・∽ｿ｡繧貞凄隱咲｢ｺ隱・|
| B02 | Service Role fail closed | 譛ｪ遒ｺ隱・| `supabase_client.py` 縺ｨunit test縲∵悽逡ｪ險ｭ螳壹メ繧ｧ繝・け霑ｽ蜉 | 螳溯ｵｷ蜍慕腸蠅・悴讀懆ｨｼ | staging縺ｧkey縺ｪ縺苓ｵｷ蜍墓拠蜷ｦ遒ｺ隱・|
| B03 | Frontend逶ｴ謗･DB | 譛ｪ遒ｺ隱・| profile隱ｭ蜿悶・Supabase client | RLS縺ｫ萓晏ｭ・| profiles policy繧貞ｮ櫂B逶｣譟ｻ |
| B04 | 繧ｨ繝ｩ繝ｼ諠・ｱ | 譛ｪ遒ｺ隱・| 隱崎ｨｼ/onboarding/callback荳闊ｬ蛹悶「nit test霑ｽ蜉 | 莉泡PI繝ｻproxy繝ｭ繧ｰ蜈ｨ菴薙・譛ｪ遒ｺ隱・| 蜈ｬ髢狗腸蠅・〒萓句､悶→繧｢繧ｯ繧ｻ繧ｹ繝ｭ繧ｰ繧堤｢ｺ隱・|
| C01 | OAuth scopes | 荳榊粋譬ｼ | `gmail.readonly`縺ｯRestricted縲～gmail.send`縺ｯSensitive | 螟夜Κ蜈ｬ髢九・verification隕∽ｻｶ | Console scope/verification繧堤｢ｺ螳壹Ｓeadonly縺ｮ繧ｵ繝ｼ繝舌・菫晏ｭ倥・security assessment隕∝凄繧ら｢ｺ隱・|
| C02 | token菫晏ｭ・| 荳榊粋譬ｼ | 繧｢繝励Μ證怜捷蛹・tenant binding/骰ｵrotation unit test霑ｽ蜉縲∵里蟄伜ｹｳ譁・・fail closed | 譌｢蟄倥ョ繝ｼ繧ｿ遘ｻ陦後・provider譖ｴ譁ｰ繝ｻ譛ｬ逡ｪ骰ｵ邂｡逅・悴螳・| 遘ｻ陦後Μ繝上・繧ｵ繝ｫ縲〉econnect/refresh螳溯ｨｼ蠕後↓驕ｩ逕ｨ |
| C03 | disconnect/revoke | 荳榊粋譬ｼ | company lock縲〉evoked marker竊貞炎髯､縲∝酔荳account/client refresh邯呎価霑ｽ蜉 | provider謌仙粥縺ｨmarker菫晏ｭ倬俣髫懷ｮｳ/譌｢螟ｱ蜉ｹ蠕ｩ譌ｧ譛ｪ螳・| 螳殱chema/provider縺ｧ繝ｩ繧､繝輔し繧､繧ｯ繝ｫ讀懆ｨｼ |
| C04 | 蟾ｮ蛻・酔譛・| 荳榊粋譬ｼ | thread縺斐→蜈ｨ蜿門ｾ励［ax 50 | 驕・ｻｶ縲〈uota縲∵ｬ關ｽ | cursor/history strategy縲｝agination縲〉ate limit |
| C05 | 騾∽ｿ｡蜀ｪ遲画ｧ | 譛ｪ遒ｺ隱・| operation claim/unknown/SENT辣ｧ蜷・遒ｺ螳啌PC縲｝rovider莉｣譖ｿ繝・せ繝・| 螳檬mail繝ｻDB transaction譛ｪ螳溯ｨｼ | DB荳ｦ陦慶laim/遒ｺ螳壹ユ繧ｹ繝医→邂｡逅・ｸ砧ail辣ｧ蜷・|
| C06 | thread邯ｭ謖・| 譛ｪ遒ｺ隱・| threadId/header蜃ｦ逅・≠繧・| 螳檬mail譛ｪ險ｼ譏・| mock headers + test mailbox E2E |
| D01 | AI驥鷹｡・| 譛ｪ遒ｺ隱・| price evidence/number validator unit test縺ｯ縺ゅｋ | 2 LLM calls縲∝ｮ溷・蜉帶悴險ｼ譏・| one-call schema縺ｨred-team test |
| D02 | prompt injection | 荳榊粋譬ｼ | raw mail繧恥rompt縺ｸ貂｡縺・| 謖・､ｺ荵励▲蜿悶ｊ | untrusted-data delimiter/policy/validator test |
| D03 | AI雋ｻ逕ｨ/荳企剞 | 荳榊粋譬ｼ | 譛域ｬ｡逕滓・莠育ｴ・timeout/蜃ｺ蜉帑ｸ企剞/蜿鈴・oken險域ｸｬ霑ｽ蜉 | 驥鷹｡崎ｲｻ逕ｨ荳企剞繝ｻlegacy邨ｱ蜷域悴螳・| 蜈ｨ邨瑚ｷｯ莠育ｮ励→螟ｱ謨玲凾雋ｻ逕ｨ繧呈､懆ｨｼ |
| D04 | AI single source | 荳榊粋譬ｼ | old `ai_judgements`縺ｨ譁ｰanalysis豺ｷ蝨ｨ | UI/霑比ｿ｡縺ｮ荳肴紛蜷・| versioned snapshot繧剃ｿ晏ｭ倥・蜿ら・ |
| E01 | 螢ｲ荳・蛻ｩ逶・| 荳榊粋譬ｼ | `estimated_profit`遲・legacy蜷阪′谿九ｋ | 螢ｲ荳翫ｒ蛻ｩ逶翫→隱､隱・| expected_revenue/cost/profit繧痴chema/UI縺ｧ蛻・屬 |
| E02 | 邨先棡蟶ｰ螻・| 譛ｪ遒ｺ隱・| timeline/learning_logs縺ゅｊ | AI蟇・ｸ弱ｒ險ｼ譏弱〒縺阪↑縺・| 謇句虚謌先棡遒ｺ螳壹・譬ｹ諡螻･豁ｴ |
| F01 | Trial/隱ｲ驥・隗｣邏・| 荳榊粋譬ｼ | 14譌･隧ｦ逕ｨ/test Checkout/鄂ｲ蜷晃ebhook/譌ｧ譁ｰ螂醍ｴ・・蜷・譛滄俣譛ｫ隗｣邏・ｿｽ蜉 | live遖∵ｭ｢縲∝ｮ溷･醍ｴ・ｫｶ蜷域､懆ｨｼ縺ｨ蜈ｨ邨瑚ｷｯ蛻ｶ髯先悴螳・| Stripe test E2E/螂醍ｴ・・譖ｿ/譛滄剞讀懆ｨｼ |
| F02 | Account deletion | 荳榊粋譬ｼ | endpoint縺ｯ螳牙・縺ｮ縺溘ａ503蛛懈ｭ｢ | 隗｣邏・蜑企勁隕∵ｱゅ↓蟇ｾ蠢應ｸ榊庄 | audited transactional RPC + retention policy |
| G01 | CORS/production URL | 譛ｪ遒ｺ隱・| runtime險ｭ螳・HTTPS/CORS fail-closed霑ｽ蜉 | 譛ｬ逡ｪorigin/HTTPS譛ｪ螳溯ｨｼ | 遒ｺ螳夂腸蠅・〒startup諡貞凄/豁｣蟶ｸ襍ｷ蜍輔ｒ讀懆ｨｼ |
| G02 | migrations/RLS/backup | 譛ｪ遒ｺ隱・| migration9譛ｬ縲・囈髮｢overlay/襍ｷ蜍不cript霑ｽ蜉縲．ocker縺ｪ縺・| 螳滄←逕ｨ/蠕ｩ蜈・悴讀懆ｨｼ | audit SQL縲｜ackup restore rehearsal |
| G03 | 隕冗ｴ・繝励Λ繧､繝舌す繝ｼ | 荳榊粋譬ｼ | 莠区･ｭ閠・∝撫蜷医○縲∽ｿ晏ｭ俶悄髢薙∝嵜螟也ｧｻ霆｢縺梧悴遒ｺ螳・| 譌･譛ｬ雋ｩ螢ｲ陦ｨ遉ｺ荳崎ｶｳ | 螳滄°逕ｨ諠・ｱ繧堤｢ｺ螳壹＠豕募ｾ狗｢ｺ隱・|
| G04 | 逶｣隕・髫懷ｮｳ騾夂衍 | 荳榊粋譬ｼ | 螳溯｣・・險ｭ螳壽悴讀懷・ | 髫懷ｮｳ縺ｫ豌励▼縺代↑縺・| error tracking, uptime, runbook |
| H01 | 螟壻ｺｺ謨ｰ/豬ｷ螟・LINE/莨夊ｨ・| 蟇ｾ雎｡螟・| 蛻晄悄雋ｩ螢ｲ遽・峇螟・| - | 1遉ｾ1user/Japan-only繧呈・險・|

## Gmail螟夜Κ謠蝉ｾ帶擅莉ｶ・・026-09-08遒ｺ隱搾ｼ・
繧ｳ繝ｼ繝峨′隕∵ｱゅ☆繧義gmail.readonly`縺ｯRestricted縲～gmail.send`縺ｯSensitive縺ｧ縺ゅｋ縲・oogle縺ｯSensitive/Restricted scope縺ｮOAuth verification繧呈ｱゅａ縲ヽestricted scope data繧偵し繝ｼ繝舌・縺ｧ菫晏ｭ倥∪縺溘・騾∽ｿ｡縺吶ｋ蝣ｴ蜷医・security assessment縺悟ｿ・ｦ√→縺励※縺・ｋ縲ょｮ滄圀縺ｮCloud Console蟇ｩ譟ｻ迥ｶ諷九∝・髢・繝・せ繝郁ｨｭ螳壹〉edirect URI縲√ヶ繝ｩ繝ｳ繝画ュ蝣ｱ縺ｯ譛ｬ逶｣譟ｻ縺ｧ縺ｯ譛ｪ遒ｺ隱阪・
## P0 tenant/RLS/onboarding 譖ｴ譁ｰ

霑ｽ蜉縺励◆譛ｪ驕ｩ逕ｨ繝輔ぃ繧､繝ｫ縺ｯ`supabase/release_readonly_tenant_audit.sql`縺ｨ`supabase/migrations/202609090001_p0_tenant_rls_onboarding.sql`縺ｧ縺ゅｋ縲ょ燕閠・・schema/policy/function/grant繧定ｪｭ繧縺縺代〒鬘ｧ螳｢繝・・繧ｿ繧貞叙蠕励＠縺ｪ縺・ょｾ瑚・・RLS繧呈怏蜉ｹ蛹悶＠縲｜rowser role縺ｮbusiness table讓ｩ髯舌ｒrevoke縲｝rofiles縺ｯ閾ｪ蟾ｱSELECT縺ｮ縺ｿ縲｛nboard_user縺ｯservice_role縺ｮ縺ｿ螳溯｡悟庄閭ｽ縺ｪSECURITY DEFINER RPC縺ｸ鄂ｮ謠帙☆繧九・
2026-09-09陬懈ｭ｣: migration縺ｯ`all tables in schema public`繧剃ｽｿ逕ｨ縺帙★縲√さ繝ｼ繝峨′菴ｿ逕ｨ縺吶ｋ11 table縺縺代ｒ譏守､ｺ縺吶ｋ縲１UBLIC/anon/authenticated縺ｮtable繝ｻcolumn privilege縲《chema CREATE縲〉ole inheritance縲」iew縲》rigger縲ヾECURITY DEFINER function縲｛nboard_user overload繧堤屮譟ｻSQL縺ｸ霑ｽ蜉縺励◆縲よ悴遏･縺ｮ蠎・＞policy縺ｯ荳諡ｬ蜑企勁縺帙★縲∥udit邨先棡縺ｧ蛻､譁ｭ縺吶ｋ縲・
驕ｩ逕ｨ蜑阪↓逶｣譟ｻSQL縺ｧ蛻励・蛻ｶ邏・・policy繝ｻowner繝ｻfunction繝ｻ驥崎､・ｒ遒ｺ隱阪☆繧九Ｕransaction蜀・・螟ｱ謨励・rollback縺吶ｋ縲・*commit蠕後・audit蜃ｺ蜉帙□縺代〒螳悟・蠕ｩ蜈・〒縺阪ｋ縺ｨ菫晁ｨｼ縺励↑縺・*縲ょ・ACL縲∫ｶ呎価繝ｭ繝ｼ繝ｫ縲ヽLS縲・未謨ｰ縲∽ｾ晏ｭ椀bject繧貞性繧schema/ACL騾驕ｿ縺ｨ蠕ｩ蜈・庄閭ｽbackup縲・囈髮｢蠕ｩ譌ｧ貍皮ｿ偵′蠢・ｦ√よ眠隕城∽ｿ｡險ｼ霍｡繧奪ROP縺励※謌ｻ縺輔↑縺・・
髫秘屬DB縺ｧ縺ｮJWT A/B螳溯ｨｼ縺ｯ譛ｪ螳滓命縲４upabase CLI 2.117.0縺ｯ螳溯｡檎｢ｺ隱肴ｸ医∩縲．ocker/psql縺ｯ譛ｪ蟆主・縲らｵｱ蜷医ユ繧ｹ繝医・譏守､ｺ險ｱ蜿ｯ繝ｻ謗･邯壼・螳悟・荳閾ｴ繝ｻloopback:54321繧定ｦ∵ｱゅ＠縲、uth邂｡逅・PI縺ｧ譫ｶ遨ｺ繝ｦ繝ｼ繧ｶ繝ｼ繧剃ｽ懈・縺励◆蠕後・壼ｸｸ縺ｮpassword login縺ｧJWT繧偵Γ繝｢繝ｪ蜀・叙蠕励☆繧九よ焔菴懈･ｭJWT縺ｯ荳崎ｦ√Ｎigration髱咏噪繝・せ繝医→謗･邯壼・繧ｬ繝ｼ繝疫nit test縺ｯRLS蜷域ｼ縺ｮ險ｼ諡縺ｧ縺ｯ縺ｪ縺・りｵｷ蜍不cript縺ｯDocker荳榊惠縺ｧDB菴懈・蜑阪↓蛛懈ｭ｢縲よ焔鬆・・OWNER_ACTIONS.md蜿ら・縲・
- [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes?authuser=993749347)・・026-09-08遒ｺ隱搾ｼ・- [OAuth verification help](https://support.google.com/cloud/answer/13463073?hl=en)・・026-09-08遒ｺ隱搾ｼ・- [Google Workspace API user data policy](https://developers.google.com/workspace/workspace-api-user-data-developer-policy?hl=en)・・026-09-08遒ｺ隱搾ｼ・- [Gmail API quota](https://developers.google.com/workspace/gmail/api/reference/quota)・・026-09-08遒ｺ隱搾ｼ・
## 雋ｻ逕ｨ繝｢繝・Ν・井ｻｮ螳壹ょｮ滓ｸｬ繝ｻ隕狗ｩ阪〒縺ｯ縺ｪ縺・ｼ・
譛磯｡榊｣ｲ荳翫・3遉ｾ=59,400蜀・・0遉ｾ=198,000蜀・・0遉ｾ=990,000蜀・ｼ育ｨ手ｾｼ・峨よｱｺ貂医・AI繝ｻ繧､繝ｳ繝輔Λ縺ｮ蜊倅ｾ｡縺ｯ繝ｪ繝昴ず繝医Μ縺ｫ蝗ｺ螳壼､縺後↑縺・◆繧√∵ｬ｡蠑上〒隧穂ｾ｡縺吶ｋ縲・
`邊怜茜蜑阪さ繧ｹ繝・= 蝗ｺ螳壹う繝ｳ繝輔Λ雋ｻ F + 鬘ｧ螳｢謨ｰ N ﾃ・(AI譛磯｡榊､牙虚雋ｻ A + Gmail/DB螟牙虚雋ｻ G) + 豎ｺ貂亥｣ｲ荳・ﾃ・豎ｺ貂域侭邇・P`

| 鬘ｧ螳｢謨ｰ | 螢ｲ荳奇ｼ育ｨ手ｾｼ・・| 豎ｺ貂郁ｲｻ | AI/Gmail/DB | 蝗ｺ螳夊ｲｻ |
|---:|---:|---:|---:|---:|
| 3 | 59,400蜀・| `59,400ﾃ猶` | `3ﾃ・A+G)` | `F` |
| 10 | 198,000蜀・| `198,000ﾃ猶` | `10ﾃ・A+G)` | `F` |
| 50 | 990,000蜀・| `990,000ﾃ猶` | `50ﾃ・A+G)` | `F` |

荳企剞譯・ 1遉ｾ1 Gmail縲∵焔蜍暮∽ｿ｡縺ｮ縺ｿ縲∵律谺｡蜷梧悄蝗樊焚繝ｻ譛域ｬ｡AI蛻・梵莉ｶ謨ｰ繝ｻ譛ｬ譁・聞繧痴erver蛛ｴ縺ｧ荳企剞蛹悶☆繧九よ焚蛟､縺ｯOpenAI螂醍ｴ・腰萓｡縲；mail quota縲∝ｹｳ蝮・せ繝ｬ繝・ラ驥上ｒ險域ｸｬ蠕後↓豎ｺ繧√ｋ縲・
## 繝槭せ繧ｿ繝ｼ蛻､譁ｭ縺悟ｿ・ｦ√↑莠矩・
1. Google Cloud OAuth verification/security assessment縺ｮ逕ｳ隲句庄蜷ｦ縲∬ｲｻ逕ｨ縲∬ｲｬ莉ｻ閠・・2. 豎ｺ貂井ｺ区･ｭ閠・・4譌･trial縲∫ｨ手ｾｼ陦ｨ遉ｺ縲∬ｧ｣邏・ｾ後・髢ｲ隕ｧ/蜑企勁譛滄剞縲・3. 繝・・繧ｿ菫晏ｭ俶悄髢薙√ヰ繝・け繧｢繝・・菫晄戟縲、I/豬ｷ螟門ｧ碑ｨ励・螳滓・縲∝撫蜷医○遯灘哨縲∬ｲｩ螢ｲ閠・ュ蝣ｱ縲・4. 蛻晄悄3遉ｾ縺ｸ縺ｮ謇句虚險ｭ螳壹・蜷梧悄螟ｱ謨玲凾縺ｮ驕狗畑諡・ｽ薙→SLA縲・5. 縲悟女豕ｨ隕玖ｾｼ鬘阪阪悟女豕ｨ鬘阪阪悟・驥鷹｡阪阪檎ｲ怜茜逶翫阪・讌ｭ蜍吝ｮ夂ｾｩ縺ｨ蜈･蜉幄ｲｬ莉ｻ閠・・# 譛譁ｰ螳溯｣・､懆ｨｼ 2026-09-10

`SALES_RELEASE_FINAL.md`繧呈怙譁ｰGate縺ｨ縺吶ｋ縲・12 passed / 19 skipped縲∝梛讀懈渊/lint/build謌仙粥縲ょｮ櫂B繝ｻ螳檬oogle繝ｻStripe test E2E譛ｪ螳溯ｨｼ縲√さ繝ｼ繝画ｮ倶ｻｶ縺ゅｊ縲∬ｲｩ螢ｲ荳榊庄縲ゆｻ･荳九・譌ｧ逶｣譟ｻ莉ｶ謨ｰ繧呈怙譁ｰ蛟､縺ｨ豺ｷ蜷後＠縺ｪ縺・・# 譛譁ｰ讀懆ｨｼ邨先棡縺ｮ陬懈ｭ｣

譛譁ｰ縺ｯ **113 passed / 19 skipped**・・026-09-10・峨・inancialSummary譛滄俣謖・ｮ壹・蜴滉ｾ｡陦ｨ遉ｺ霑ｽ蜉蠕後ｂTypeScript / ESLint / production build謌仙粥縲ゆｻ･荳九・112莉ｶ縺ｯ逶ｴ蜑阪メ繧ｧ繝・け繝昴う繝ｳ繝医・螻･豁ｴ縲ょｮ櫂B繝ｻ隱崎ｨｼ蠕袈I縺ｯ譛ｪ螳溯ｨｼ縲りｲｩ螢ｲ荳榊庄縲りｩｳ邏ｰ縺ｯSALES_RELEASE_FINAL.md縲・
