# FinSight.ai — Project Context

## Что это

AI-powered финансовый продукт для фаундеров и фрилансеров. Отвечает на вопрос: "Сколько месяцев я могу прожить на то, что у меня есть?"

**Pull-модель**: пользователь сам инициирует анализ → вводит данные → получает runway, cashflow, AI-рекомендации за 30 секунд.

---

## Ссылки

- **Лендинг**: https://finsight-landing.vercel.app
- **Приложение**: https://finsight-ai-tawny.vercel.app
- **Код**: `/Projects/finsight-ai/`

---

## Стек

| Слой | Технология |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Mobile/Web | React Native + Expo |
| Validation | Pydantic (Python) + Zod (TypeScript) |
| AI | OpenAI-compatible LLM (explanation only) |
| Deploy (backend) | Railway |
| Deploy (frontend) | Vercel |

---

## Архитектура

```
User Input
  → core-engine       (детерминированная математика: cashflow, runway, projection)
  → scenario-engine   (симуляция "что если": один поведенческий сценарий)
  → validation-gateway (схема + safety gate)
  → ai-layer          (LLM объясняет — никогда не считает)
  → UI decision screen
```

**Ключевое правило:** AI никогда не считает финансы. Только объясняет то, что уже посчитал engine.

---

## Структура пакетов

```
packages/
├── core-engine/        # Детерминированная математика (cashflow, savings_rate, projection)
├── scenario-engine/    # Симуляция поведенческих изменений
├── ai-layer/           # LLM wrapper (объяснение, не вычисление)
├── validation-gateway/ # Schema + hallucination guard + quality scoring
├── shared-types/       # Общие модели данных (Pydantic)
├── analytics/          # Event tracking (сессии, воронка, AI health)
└── config/             # Глобальный конфиг
```

---

## API Endpoints

| Endpoint | Метод | Описание |
|---|---|---|
| `/baseline` | POST | Детерминированный финансовый baseline |
| `/scenario` | POST | Симуляция одного поведенческого изменения |
| `/explain` | POST | AI объяснение результата |
| `/decision` | POST | Логирование решения пользователя |
| `/events` | POST | Аналитические события |
| `/analytics/session/{id}` | GET | Сводка по сессии |
| `/analytics/funnel/{id}` | GET | Воронка по сессии |
| `/analytics/ai-health` | GET | Качество AI outputs |
| `/health` | GET | Liveness probe |

---

## Гарантии системы

| Гарантия | Как обеспечена | Чем проверено |
|---|---|---|
| AI не считает финансы | Промпт + **numeric_guard**: whitelist из пяти значений, которые промпт разрешает называть. Всё остальное — месяцы, суммы, проценты, числительные словами, «about a year», недели — отклоняется и уходит в fallback | 12 adversarial-кейсов, gate = 100% |
| Engine — единственный источник правды | Архитектурный контракт; whitelist строится только из engine output | 30 clean-кейсов, false rejection ≤ 2% |
| Никаких advisor-формулировок | **language_guard**: блокирующий тир («you should», «I recommend», «guaranteed», «financial advisor», «invest in stocks») → fallback; мягкий тир («consider», «make sure») → вычет в скоринге | 5 adversarial-кейсов, gate = 100% |
| Все outputs schema-validated | Pydantic + Zod | 3 adversarial-кейса |
| /explain никогда не возвращает 5xx | try/except в роутере + все транспортные ошибки сводятся к AILayerError + ленивое создание клиента (нет ключа → mock, а не падение на импорте) | 6 adversarial-кейсов, gate = 100% |
| Latency baseline < 300ms | TimingMiddleware, бюджет из `shared_types.sla` | измеряется |
| Latency explain < 3000ms | Дедлайн в LLM-клиенте (80% бюджета) + p50/p95 в `/analytics/ai-health` | gate по p95 |

---

## Экраны мобильного приложения

```
/onboarding → /goal → /input → /baseline → /scenario → /decision
```

---

## Статус

- ✅ Лендинг задеплоен (Vercel)
- ✅ Приложение задеплоен (Vercel)
- ✅ Все пакеты реализованы
- ✅ API endpoints рабочие
- ✅ validation-gateway: numeric whitelist, language guard, schema validation, NaN checks
- ✅ ai-layer: `llm_client.py` с дедлайном под SLA. Переключение автоматическое: есть `OPENAI_API_KEY` → реальный клиент, нет → mock. `# SWAP THIS` больше нет.
- ✅ eval framework: 56 замороженных кейсов, 6 гейтов, `make eval`, гейт в CI
- ✅ Rate limit по IP + дневной бюджет на `/explain`
- ✅ Аналитика: путь БД из `FINSIGHT_DB_PATH` (было `/tmp` — стиралось каждым деплоем), `/decision` теперь попадает и в воронку
- ⚠️ **Осталось руками:** `OPENAI_API_KEY` и `FINSIGHT_DB_PATH` (volume) в Railway; `EXPO_PUBLIC_API_URL` в Vercel project settings + редеплой
- ⚠️ Фронтовая аналитика не подключена (нет реальных пользователей)

---

## Ключевые находки из кода

### ai-layer промпт (system prompt)
Очень строгий — AI не может:
- Генерировать числа не из input JSON
- Использовать "should", "recommend", "consider", "advisor"
- Выражать уверенность (только "based on these figures", "at this rate")
- Писать больше 2-3 предложений
- Писать числа словами или округлять их
- Возвращать что-то кроме JSON

Output — **шесть полей**: recommendation, explanation, summary, confidence,
reasoning, key_assumptions. Раньше промпт просил два, а scorer снимал баллы за
отсутствие остальных четырёх: потолок качества был 70 из 100, статус «approved»
был недостижим в принципе.

### validation-gateway — numeric guard (whitelist)
Каждое число в тексте модели должно сводиться к одному из пяти значений, которые
промпт разрешает называть. Диапазона нет — величина числа не имеет значения.

Разбирает деньги (`$1,200`, `299.5`), проценты, длительности цифрами и словами,
«about a year», недели и дни. Проверяет **все** поля модели, включая `reasoning`
и `key_assumptions`.

Прежняя эвристика (целые в [3, 500], с исключением для `$` и `%`) пропускала
«your runway is 2 months», «cut $900», «at 85% adherence», «eighteen months» —
и ложно срабатывала на `$1,200`, читая его как 200 месяцев.

Плюс NaN/Infinity checks, adherence bounds [0.1, 0.95], delta consistency.

### eval framework (`evals/`)
56 замороженных кейсов: 30 clean (ловят ложные отклонения) + 26 adversarial
(ловят пропуски), разбитые по классам отказа: numeric, language, schema,
transport. 6 гейтов, exit code работает как CI-гейт. Отчёт всегда указывает
режим — mock или live: latency, измеренная на моке, это не latency.
Подробнее — `evals/README.md`.

### Events логируются в stdout
Формат: `{"event": "BASELINE_COMPUTED", "timestamp": "...", "payload": {...}}`
События: BASELINE_COMPUTED, SCENARIO_SIMULATED, AI_EXPLANATION_GENERATED, RECOMMENDATION_ACCEPTED, RECOMMENDATION_REJECTED

---

## Как включить реальный LLM

Кода писать не нужно:

1. Добавить `OPENAI_API_KEY` в Railway environment variables.
2. Всё. `get_llm_client()` подхватит ключ на первом вызове; без ключа
   продолжает работать mock — без падений и без 5xx.
3. Замерить: `OPENAI_API_KEY=... make eval-live`. Оттуда берутся честные
   p50/p95 и fallback_rate.

Опционально: `FINSIGHT_LLM_MODEL` (по умолчанию `gpt-4o-mini`),
`FINSIGHT_FORCE_MOCK=1` чтобы принудительно оставить mock.

Все переменные и что происходит при их отсутствии — `docs/OPERATIONS.md`.

<details>
<summary>Как это выглядело раньше (историческая справка)</summary>

1. Создать `packages/ai-layer/ai_layer/llm_client.py`:
```python
import openai

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def call(self, system_prompt: str, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
```

2. В `ai_layer/explain.py` найти строку `# SWAP THIS` и заменить:
```python
# было:
_llm_client = MockLLMClient(mode="valid")  # SWAP THIS
# стало:
from ai_layer.llm_client import OpenAIClient
_llm_client = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
```

3. Добавить `OPENAI_API_KEY` в Railway environment variables

Проблема этого варианта: `os.environ["OPENAI_API_KEY"]` на уровне модуля роняет
импорт — а значит и весь FastAPI, включая `/health`, — если переменная не задана.

</details>

---

## Позиционирование (для CV и LinkedIn)

- **Роль Mark**: AI PM (founding team)
- **Команда**: небольшая команда, Mark отвечает за продукт и AI-слой
- **Запуск**: 0→1 за 8 недель
- **Ключевые метрики**: заполнить из `make eval-live` — p50/p95 latency,
  numeric_fidelity_rate, fallback_rate. Прежние «<3s latency» и «~95% schema
  compliance» измерялись на `MockLLMClient(mode="valid")` — клиенте, который
  отвечает мгновенно и по построению валидно. Цитировать их нельзя.
- **Монетизация**: freemium → $7.99/mo, сценарный пейволл, target 4-6% конверсия

---

## Следующие шаги

1. `EXPO_PUBLIC_API_URL` в Vercel project settings + редеплой (переменная билд-тайм, править `.env` бесполезно)
2. `OPENAI_API_KEY` + `FINSIGHT_DB_PATH` (volume) в Railway
3. `make eval-live` → подставить измеренные цифры в CV и в пост
4. Vercel Analytics / PostHog + 6 событий фронтовой воронки
5. Найти первых demo-users (пост публиковать только после 1–3)
6. Добавить интеграцию с Plaid/Open Banking (убрать ручной ввод)

---

## LinkedIn пост (готов к публикации)

```
Two weeks ago I posted about building FinSight.ai.

It's live now.

Here's what the team learned shipping it:

The hardest part wasn't the LLM integration or the FastAPI backend.
It was making AI output that a non-technical founder would actually trust.

We solved it by separating concerns completely:
— deterministic engine does all the math (no AI touches numbers)
— LLM only explains what the engine already computed
— every output schema-validated before it hits the UI

Result: runway calculation in under 30 seconds. Structured output. No hallucinations on financial data.

If you're a founder or freelancer who's ever done late-night bank balance math — try it:
[ссылка в комментарии]

Free. No signup. 2 minutes. We'd love your honest feedback.

#BuildInPublic #AIProduct #Founders
```
