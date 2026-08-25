# APE-SECURITY-OBS-001
## read_file action lacks path containment enforcement

**ID**: APE-SECURITY-OBS-001
**Title**: read_file action lacks path containment enforcement
**Status**: OPEN / OBSERVED
**Classification**: PRE-EXISTING SECURITY GAP
**Discovery**: Sandbox-to-Host Path Translation audit (2026-08-25)
**Affected Component**: ApeCoderAgent read_file action

## Evidence
- `src/ape/intelligence/execution/agent.py:188` (ApeCoderAgent) eylem `read_file` olduğunda `params["path"]` doğrudan `cat` shell komutuna formatlanmaktadır:
  `elif proposed_action == "read_file" and params.get("path"): cmd = f'cat {json.dumps(params["path"])}'`
- `src/ape/intelligence/execution/agent.py:166` (Translation öncesinde 162. satır) içerisinde `validate_path_containment()` koruması AÇIKÇA yalnızca `create_file` ve `modify_file` işlemleriyle sınırlandırılmıştır:
  `if proposed_action in ("create_file", "modify_file") and params.get("path"):`
- `git show HEAD~1:src/ape/intelligence/execution/agent.py` incelendiğinde bu durumun translation implementation'ından önce de aynı olduğu kanıtlanmıştır. Orijinal kodda da `read_file` action'ı için hiçbir guard fonksiyonu çağrılmamaktadır.

## Security Impact
Potential unauthorized file read / information disclosure if read_file accepts paths outside the project workspace. Severity NOT YET DETERMINED — exploitability henüz adversarial olarak test edilmedi (bkz. Recommended Future Action).

## Important
Bu bulgu mevcut Sandbox-to-Host Path Translation remediation tarafından OLUŞTURULMAMIŞTIR ve bu commit tarafından ÇÖZÜLMEMEKTEDİR. Translation, read_file'ın path'ini de çeviriyor (namespace normalizasyonu için) ama bu çeviri güvenlik kararı vermiyor — read_file zaten hiçbir containment guard'ından geçmiyordu, geçmeye de başlamadı.

## Current Mitigation
APE framework katmanında (Execution Engine / Policy / Agent) `read_file` için HİÇBİR açık mitigation bulunmamaktadır.
Hedef platforma bağlı olarak pasif kısıtlamalar mevcuttur:
- `DockerSandboxExecutor` kullanıldığında: Docker container'ın kendi filesystem izolasyonu vardır. Ajan `project_root` dışındaki host dosyalarına erişemez, ancak container içindeki sistem dosyalarını (örn: `/etc/passwd`) okuyabilir.
- `LocalTestSandboxExecutor` veya herhangi bir Host-native executor kullanıldığında: Hiçbir izolasyon yoktur. Ajan traversal (`../`) kullanarak Host işletim sistemindeki herhangi bir dosyayı okuyabilir (yetki yettiği sürece).

## Recommended Future Action
read_file için explicit path containment policy tasarlanması (muhtemelen validate_path_containment()'ın create_file/modify_file ile aynı şekilde read_file'a da uygulanması) ve adversarial testlerle gerçek exploitability'nin ölçülmesi — ayrı bir READ-ONLY audit veya implementation turu olarak, bu commit'in kapsamı dışında.

## Out of Scope
Bu commit'te read_file security behavior DEĞİŞTİRİLMEZ. Sadece mevcut, önceden var olan boşluk resmi olarak kayda geçirilir.

## Related
- Sandbox-to-Host Path Translation remediation (bu oturum)
- RFC-020 boundary safety
- ORION-146 execution authorization boundary
