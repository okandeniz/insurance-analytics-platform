# Insurance Analytics Platform

Otomobil sigortası portföyünü uçtan uca analiz eden; veri temizleme, MySQL veri modeli, SQL analizleri, makine öğrenmesi, beklenen zarar hesabı, Power BI raporu, FastAPI servisi ve Streamlit arayüzünü bir araya getiren analitik platform.

Projenin iki temel modelleme amacı vardır:

- Bir sözleşmede hasar oluşup oluşmayacağını incelemek (`claim occurrence` / frekans).
- Bildirilmiş bir hasarın tutarını tahmin etmek (`claim severity` / hasar şiddeti).

Mevcut veri setinde bireysel hasar oluşum modeli test verisine güvenilir biçimde genellenemediği için portföy düzeyindeki beklenen zarar hesabında daha sade ve kararlı bir yaklaşım seçilmiştir:

```text
Beklenen Zarar = Eğitim Portföyü Hasar Oranı × Eğitim Portföyü Ortalama Hasar Tutarı
```

Bildirilmiş hasarlar için kullanılan servis modeli ise logaritmik hedef dönüşümlü bir Random Forest regresyon modelidir.

## Mimari ve veri akışı

```text
Ham CSV dosyaları
    │
    ▼
Python veri temizleme ve doğrulama
    │
    ▼
İşlenmiş CSV dosyaları
    │
    ▼
MySQL tabloları ──► SQL görünümleri ──► Power BI
                         │
                         ├──► Jupyter EDA ve modelleme
                         │
                         ├──► Beklenen zarar çıktıları
                         │
                         └──► Severity modeli (.joblib)
                                      │
                                      ▼
                               FastAPI /predict
                                      │
                                      ▼
                                Streamlit arayüzü
```

## Öne çıkan bileşenler

- Veri kalitesi: para alanlarının, farklı tarih biçimlerinin, kategorik değerlerin ve araç gücü birimlerinin standardizasyonu; anahtar, tarih ve referans bütünlüğü kontrolleri.
- SQL katmanı: sözleşme, hasar ve araç tabloları; raporlama ve makine öğrenmesi için zenginleştirilmiş görünümler.
- Claim occurrence: dengesiz sınıf problemi için PR-AUC ve ROC-AUC odaklı model karşılaştırmaları.
- Claim severity: sayısal imputasyon/ölçekleme, kategorik one-hot encoding ve `log1p` hedef dönüşümünü içeren tek bir scikit-learn pipeline'ı.
- Expected Loss: test portföyünden ayrılmış eğitim frekansı ve ortalama şiddet ile portföy düzeyi benchmark.
- Sunum katmanı: Power BI dashboard, FastAPI tahmin API'si ve Streamlit kullanıcı arayüzü.

## Teknolojiler

Python, pandas, NumPy, scikit-learn, XGBoost, MySQL, pyodbc, Jupyter, FastAPI, Uvicorn, Streamlit ve Power BI.

## Proje yapısı

```text
insurance-analytics-platform/
├── backend/                    # FastAPI uygulaması, şemalar ve tahmin servisi
├── dashboards/
│   └── insurance_analytics_dashboard.pbix
├── data/
│   ├── raw/                    # Kaynak contracts/claims/vehicles CSV dosyaları
│   ├── interim/
│   └── processed/              # Temiz veri ve train/test eşleme dosyaları
├── frontend/
│   └── app.py                  # Streamlit hasar tutarı tahmin arayüzü
├── models/                     # Eğitilmiş pipeline ve model metadata'sı
├── notebooks/                  # 01-07 arası analiz ve modelleme akışı
├── outputs/                    # Beklenen zarar sözleşme çıktısı ve özeti
├── scripts/
│   ├── clean_data.py
│   ├── train_claim_severity.py
│   └── generate_expected_loss.py
├── sql/
│   ├── views/                  # Analitik ve ML görünümleri
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_data_validation.sql
│   └── 04_sql_analysis.sql
└── src/
    ├── database/               # MySQL bağlantısı ve veri yükleme
    ├── features/               # Deterministik severity feature engineering
    ├── modeling/               # Model pipeline tanımı
    ├── preprocessing/          # Veri temizleme fonksiyonları
    └── utils/
```

`data/` altındaki CSV dosyaları ve `models/*.joblib` Git tarafından izlenmez. Yeni bir klonda bu dosyaların ayrıca sağlanması veya aşağıdaki akışla yeniden üretilmesi gerekir.

## Kurulum

### Gereksinimler

- Python 3.12 önerilir (notebook'lar Python 3.12.3 ile hazırlanmıştır).
- MySQL sunucusu.
- Python modelleme betikleri için `InsuranceAnalytics` adlı çalışan bir ODBC DSN.
- Dashboard'u görüntülemek için Power BI Desktop (isteğe bağlı).

Sanal ortamı oluşturup bağımlılıkları yükleyin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install mysql-connector-python python-dotenv jupyterlab
```

`mysql-connector-python` ve `python-dotenv`, `src/database/connection.py` tarafından kullanılır fakat mevcut `requirements.txt` içinde yer almamaktadır. `jupyterlab` ise notebook'ları yeniden çalıştırmak için isteğe bağlıdır.

### Ortam değişkenleri

Örnek dosyayı kopyalayın ve kendi MySQL bilgilerinizi girin:

```powershell
Copy-Item .env.example .env
```

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=insurance_analytics
```

`.env` dosyası Git tarafından yok sayılır; gerçek parolaları repoya eklemeyin.

### ODBC bağlantısı

`scripts/train_claim_severity.py` ve `scripts/generate_expected_loss.py` aşağıdaki bağlantıyı kullanır:

```python
pyodbc.connect("DSN=InsuranceAnalytics;")
```

Bu nedenle sisteminizde MySQL ODBC sürücüsünü kurup `InsuranceAnalytics` adlı DSN'i aynı veritabanına yönlendirin. Veri yükleme modülü ise ODBC yerine `.env` içindeki bilgilerle doğrudan `mysql-connector-python` kullanır.

## Uçtan uca çalıştırma

Tüm komutları proje kök dizininden çalıştırın.

### 1. Ham veriyi yerleştirin

Şu dosyaların mevcut olduğundan emin olun:

```text
data/raw/contracts.csv
data/raw/claims.csv
data/raw/vehicles.csv
```

### 2. Veriyi temizleyin

```powershell
python -m scripts.clean_data
```

Komut temizlenmiş dosyaları `data/processed/` dizinine yazar ve kritik yapısal kontrolleri çalıştırır.

### 3. Veritabanını hazırlayın

MySQL istemcinizde sırasıyla çalıştırın:

```text
sql/01_create_database.sql
sql/02_create_tables.sql
```

Ardından temizlenmiş veriyi yükleyin:

```powershell
python -m src.database.load_data
```

İsteğe bağlı veri kalite kontrolleri:

```text
sql/03_data_validation.sql
```

### 4. Analitik ve ML görünümlerini oluşturun

`sql/views/` altındaki dosyaları numara sırasıyla çalıştırın:

1. `01_vw_contracts_enriched.sql`
2. `02_vw_claims_enriched.sql`
3. `03_vw_auto_risk.sql`
4. `04_vw_auto_claim_occurrence_ml.sql`
5. `05_vw_auto_claim_severity_ml.sql`

Genel portföy sorguları için ayrıca `sql/04_sql_analysis.sql` kullanılabilir.

### 5. Notebook akışını inceleyin veya yeniden çalıştırın

```powershell
jupyter lab
```

Önerilen sıra:

1. `01_data_understanding.ipynb`
2. `02_data_cleaning.ipynb`
3. `03_claim_occurrence_eda.ipynb`
4. `04_claim_occurrence_modeling.ipynb`
5. `05_claim_severity_eda.ipynb`
6. `06_claim_severity_modeling.ipynb`
7. `07_expected_loss_modeling.ipynb`

Occurrence notebook'u, beklenen zarar betiğinin kullandığı `data/processed/occurrence_split_map.csv` dosyasını üretir.

### 6. Claim severity modelini eğitin

```powershell
python -m scripts.train_claim_severity
```

Üretilen dosyalar:

```text
models/claim_severity_pipeline.joblib
models/claim_severity_metadata.json
```

API, `claim_severity_pipeline.joblib` mevcut değilse başlatılamaz.

### 7. Beklenen zarar çıktısını üretin

```powershell
python -m scripts.generate_expected_loss
```

Betik şu çıktıları üretir:

```text
outputs/expected_loss_contracts.csv
outputs/expected_loss_summary.json
```

Ayrıca sonuçları MySQL'deki `expected_loss_results` tablosuna yazar. Bu tablo için DDL mevcut SQL dosyalarında yer almadığından tabloyu önceden oluşturun:

```sql
USE insurance_analytics;

CREATE TABLE IF NOT EXISTS expected_loss_results (
    contract_id   VARCHAR(20)    NOT NULL,
    dataset       VARCHAR(10)    NOT NULL,
    has_claim     BOOLEAN        NOT NULL,
    expected_loss DECIMAL(14, 4) NOT NULL,
    actual_loss   DECIMAL(14, 2) NOT NULL,
    PRIMARY KEY (contract_id),
    CONSTRAINT fk_expected_loss_contract
        FOREIGN KEY (contract_id)
        REFERENCES contracts (contract_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
```

Betik her çalıştırmada bu tablodaki mevcut kayıtları silip sonuçların tamamını yeniden ekler.

## API ve arayüz

Önce API'yi başlatın:

```powershell
uvicorn backend.main:app --reload
```

- Sağlık kontrolü: `http://127.0.0.1:8000/health`
- Swagger arayüzü: `http://127.0.0.1:8000/docs`
- Tahmin endpoint'i: `POST http://127.0.0.1:8000/predict`

Örnek istek:

```json
{
  "occurrence_date": "2025-06-15",
  "claim_type": "Collision",
  "risk_zone": "Medium",
  "channel": "Agency",
  "csp": "Employee",
  "gender": "Female",
  "brand": "Renault",
  "fuel_type": "Gasoline",
  "vehicle_usage": "Personal",
  "annual_premium": 720.5,
  "client_age": 37,
  "power_hp": 120,
  "vehicle_age_at_claim": 4,
  "current_value": 18500,
  "previous_claims": 1,
  "declaration_lag_days": 3
}
```

Örnek yanıt:

```json
{
  "predicted_damage_amount": 4360.47,
  "model_name": "Random Forest - Log Target Severity Model",
  "usage": "Post-claim triage and reserve support"
}
```

API çalışırken ikinci bir terminalde Streamlit arayüzünü açın:

```powershell
streamlit run frontend/app.py
```

Arayüz varsayılan olarak `http://127.0.0.1:8000/predict` adresine istek gönderir.

## Model sonuçları

Depodaki mevcut notebook ve çıktı artefaktlarına göre:

| Çalışma | Sonuç |
|---|---:|
| Occurrence test PR-AUC | 0.0204 |
| Occurrence test ROC-AUC | 0.4510 |
| Test portföyü hasar oranı | 0.0208 |
| Severity test MAE | 973.60 |
| Severity test RMSE | 1,473.34 |
| Severity test R² | 0.8727 |
| Sözleşme başına beklenen zarar | 91.80 |
| Beklenen toplam test zararı | 79,499.85 |
| Gerçekleşen toplam test zararı | 90,158.33 |
| Mutlak yüzde hata | %11.82 |
| Actual / Expected | 1.1341 |

Occurrence modelinin test performansı taban hasar oranına yakın kaldığı için bireysel olasılık tahminleri üretim yaklaşımına taşınmamıştır. Severity sonucu umut verici olsa da model yalnızca 109 hasar kaydıyla eğitildiğinden metrikler dikkatli yorumlanmalıdır. En güçlü severity belirleyicisi `claim_type` değişkenidir.

## Kullanım amacı ve sınırlamalar

- `/predict` endpoint'i bir hasar bildirildikten sonra erken triyaj ve rezerv desteği içindir; sözleşme başlangıcında fiyatlama modeli olarak tasarlanmamıştır.
- Çıktılar karar desteği sağlar; eksper değerlendirmesinin veya aktüeryal rezerv sürecinin yerine geçmez.
- Beklenen zarar modeli şu anda tüm uygun Auto sözleşmelerine aynı portföy benchmark'ını uygular.
- API'nin CORS listesi yalnızca `localhost:5500` ve `127.0.0.1:5500` adreslerini içerir. Streamlit sunucu taraflı istek yaptığı için bundan etkilenmez; tarayıcı tabanlı farklı istemciler için liste güncellenmelidir.
- Projede henüz otomatik test paketi ve CI yapılandırması bulunmamaktadır.

## Power BI

`dashboards/insurance_analytics_dashboard.pbix` dosyası portföy, hasar ve araç risk analizlerini görselleştirir. Raporu yenilemeden önce MySQL bağlantısının ve ilgili SQL görünümlerinin erişilebilir olduğundan emin olun.

---

# Insurance Analytics Platform — English

An end-to-end analytics platform for automobile insurance portfolios, combining data cleaning, a MySQL data model, SQL analysis, machine learning, expected loss calculation, a Power BI report, a FastAPI service, and a Streamlit interface.

The project has two primary modeling objectives:

- Analyze whether a claim will occur for a contract (`claim occurrence` / frequency).
- Estimate the amount of a reported claim (`claim severity`).

Because the individual claim occurrence model did not generalize reliably to the test data, the portfolio-level expected loss calculation uses a simpler and more stable approach:

```text
Expected Loss = Training Portfolio Claim Rate × Training Portfolio Mean Claim Amount
```

For reported claims, the prediction service uses a Random Forest regression model with a logarithmic target transformation.

## Architecture and data flow

```text
Raw CSV files
    │
    ▼
Python data cleaning and validation
    │
    ▼
Processed CSV files
    │
    ▼
MySQL tables ──► SQL views ──► Power BI
                      │
                      ├──► Jupyter EDA and modeling
                      │
                      ├──► Expected loss outputs
                      │
                      └──► Severity model (.joblib)
                                   │
                                   ▼
                            FastAPI /predict
                                   │
                                   ▼
                           Streamlit interface
```

## Key components

- Data quality: standardization of monetary fields, mixed date formats, categorical values, and vehicle power units; key, date, and referential integrity checks.
- SQL layer: contract, claim, and vehicle tables; enriched views for reporting and machine learning.
- Claim occurrence: model comparisons focused on PR-AUC and ROC-AUC for the imbalanced classification problem.
- Claim severity: a single scikit-learn pipeline containing numerical imputation/scaling, categorical one-hot encoding, and a `log1p` target transformation.
- Expected Loss: a portfolio-level benchmark based on training frequency and mean severity, isolated from the test portfolio.
- Presentation layer: a Power BI dashboard, FastAPI prediction API, and Streamlit user interface.

## Technologies

Python, pandas, NumPy, scikit-learn, XGBoost, MySQL, pyodbc, Jupyter, FastAPI, Uvicorn, Streamlit, and Power BI.

## Project structure

```text
insurance-analytics-platform/
├── backend/                    # FastAPI application, schemas, and prediction service
├── dashboards/
│   └── insurance_analytics_dashboard.pbix
├── data/
│   ├── raw/                    # Source contracts/claims/vehicles CSV files
│   ├── interim/
│   └── processed/              # Clean data and train/test mapping files
├── frontend/
│   └── app.py                  # Streamlit claim amount prediction interface
├── models/                     # Trained pipeline and model metadata
├── notebooks/                  # Analysis and modeling workflow, numbered 01-07
├── outputs/                    # Contract-level expected loss output and summary
├── scripts/
│   ├── clean_data.py
│   ├── train_claim_severity.py
│   └── generate_expected_loss.py
├── sql/
│   ├── views/                  # Analytical and ML views
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_data_validation.sql
│   └── 04_sql_analysis.sql
└── src/
    ├── database/               # MySQL connection and data loading
    ├── features/               # Deterministic severity feature engineering
    ├── modeling/               # Model pipeline definition
    ├── preprocessing/          # Data-cleaning functions
    └── utils/
```

CSV files under `data/` and `models/*.joblib` are not tracked by Git. In a fresh clone, these files must either be provided separately or regenerated by following the workflow below.

## Installation

### Requirements

- Python 3.12 is recommended (the notebooks were created with Python 3.12.3).
- A MySQL server.
- A working ODBC DSN named `InsuranceAnalytics` for the Python modeling scripts.
- Power BI Desktop to view the dashboard (optional).

Create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install mysql-connector-python python-dotenv jupyterlab
```

`mysql-connector-python` and `python-dotenv` are used by `src/database/connection.py` but are not included in the current `requirements.txt`. `jupyterlab` is optional and is only needed to rerun the notebooks.

### Environment variables

Copy the example file and enter your MySQL credentials:

```powershell
Copy-Item .env.example .env
```

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=insurance_analytics
```

The `.env` file is ignored by Git. Do not commit real passwords to the repository.

### ODBC connection

`scripts/train_claim_severity.py` and `scripts/generate_expected_loss.py` use the following connection:

```python
pyodbc.connect("DSN=InsuranceAnalytics;")
```

Install a MySQL ODBC driver on your system and configure a DSN named `InsuranceAnalytics` that points to the same database. The data-loading module does not use ODBC; it connects directly through `mysql-connector-python` with the settings in `.env`.

## End-to-end execution

Run all commands from the project root directory.

### 1. Add the raw data

Make sure the following files exist:

```text
data/raw/contracts.csv
data/raw/claims.csv
data/raw/vehicles.csv
```

### 2. Clean the data

```powershell
python -m scripts.clean_data
```

This command writes the cleaned files to `data/processed/` and runs critical structural validations.

### 3. Prepare the database

Run the following files in your MySQL client, in order:

```text
sql/01_create_database.sql
sql/02_create_tables.sql
```

Then load the cleaned data:

```powershell
python -m src.database.load_data
```

Optional data-quality checks:

```text
sql/03_data_validation.sql
```

### 4. Create the analytical and ML views

Run the files under `sql/views/` in numerical order:

1. `01_vw_contracts_enriched.sql`
2. `02_vw_claims_enriched.sql`
3. `03_vw_auto_risk.sql`
4. `04_vw_auto_claim_occurrence_ml.sql`
5. `05_vw_auto_claim_severity_ml.sql`

For general portfolio queries, you can also use `sql/04_sql_analysis.sql`.

### 5. Review or rerun the notebook workflow

```powershell
jupyter lab
```

Recommended order:

1. `01_data_understanding.ipynb`
2. `02_data_cleaning.ipynb`
3. `03_claim_occurrence_eda.ipynb`
4. `04_claim_occurrence_modeling.ipynb`
5. `05_claim_severity_eda.ipynb`
6. `06_claim_severity_modeling.ipynb`
7. `07_expected_loss_modeling.ipynb`

The occurrence notebook generates `data/processed/occurrence_split_map.csv`, which is required by the expected loss script.

### 6. Train the claim severity model

```powershell
python -m scripts.train_claim_severity
```

Generated files:

```text
models/claim_severity_pipeline.joblib
models/claim_severity_metadata.json
```

The API cannot start if `claim_severity_pipeline.joblib` is missing.

### 7. Generate the expected loss output

```powershell
python -m scripts.generate_expected_loss
```

The script generates:

```text
outputs/expected_loss_contracts.csv
outputs/expected_loss_summary.json
```

It also writes the results to the `expected_loss_results` table in MySQL. Because the DDL for this table is not included in the current SQL files, create it first:

```sql
USE insurance_analytics;

CREATE TABLE IF NOT EXISTS expected_loss_results (
    contract_id   VARCHAR(20)    NOT NULL,
    dataset       VARCHAR(10)    NOT NULL,
    has_claim     BOOLEAN        NOT NULL,
    expected_loss DECIMAL(14, 4) NOT NULL,
    actual_loss   DECIMAL(14, 2) NOT NULL,
    PRIMARY KEY (contract_id),
    CONSTRAINT fk_expected_loss_contract
        FOREIGN KEY (contract_id)
        REFERENCES contracts (contract_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
```

Each run deletes all existing records from this table before inserting the complete new result set.

## API and interface

Start the API first:

```powershell
uvicorn backend.main:app --reload
```

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Prediction endpoint: `POST http://127.0.0.1:8000/predict`

Example request:

```json
{
  "occurrence_date": "2025-06-15",
  "claim_type": "Collision",
  "risk_zone": "Medium",
  "channel": "Agency",
  "csp": "Employee",
  "gender": "Female",
  "brand": "Renault",
  "fuel_type": "Gasoline",
  "vehicle_usage": "Personal",
  "annual_premium": 720.5,
  "client_age": 37,
  "power_hp": 120,
  "vehicle_age_at_claim": 4,
  "current_value": 18500,
  "previous_claims": 1,
  "declaration_lag_days": 3
}
```

Example response:

```json
{
  "predicted_damage_amount": 4360.47,
  "model_name": "Random Forest - Log Target Severity Model",
  "usage": "Post-claim triage and reserve support"
}
```

While the API is running, open the Streamlit interface in a second terminal:

```powershell
streamlit run frontend/app.py
```

By default, the interface sends requests to `http://127.0.0.1:8000/predict`.

## Model results

Based on the current notebook and output artifacts in the repository:

| Study | Result |
|---|---:|
| Occurrence test PR-AUC | 0.0204 |
| Occurrence test ROC-AUC | 0.4510 |
| Test portfolio claim rate | 0.0208 |
| Severity test MAE | 973.60 |
| Severity test RMSE | 1,473.34 |
| Severity test R² | 0.8727 |
| Expected loss per contract | 91.80 |
| Predicted total test loss | 79,499.85 |
| Actual total test loss | 90,158.33 |
| Absolute percentage error | 11.82% |
| Actual / Expected | 1.1341 |

Because the occurrence model's test performance remained close to the baseline claim rate, individual probability predictions were not carried into the final approach. The severity result is promising, but the model was trained on only 109 claim records, so its metrics should be interpreted carefully. The strongest severity predictor is `claim_type`.

## Intended use and limitations

- The `/predict` endpoint is intended for early triage and reserve support after a claim has been reported; it is not designed as a pricing model at policy inception.
- The outputs provide decision support and do not replace expert assessment or the actuarial reserving process.
- The expected loss model currently applies the same portfolio benchmark to all eligible Auto contracts.
- The API's CORS list only includes `localhost:5500` and `127.0.0.1:5500`. Streamlit is unaffected because it sends server-side requests; browser-based clients hosted elsewhere require an updated allowlist.
- The project does not yet include an automated test suite or CI configuration.

## Power BI

`dashboards/insurance_analytics_dashboard.pbix` visualizes portfolio, claim, and vehicle risk analyses. Before refreshing the report, make sure the MySQL connection and the relevant SQL views are accessible.
