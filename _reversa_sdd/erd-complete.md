# Diagrama Entidade-Relacionamento (ERD) — BFX

```mermaid
erDiagram
    PLAYLIST_FILE ||--o{ TRACK : "contém"
    TRACK ||--|| AUDIO_FILE : "gera"
    TRACK ||--|| FEATURES : "possui"

    TRACK {
        string url PK
        string title
        string artist
        string album
        string genre
        string safe_title
        float view_count
        float like_count
        float comment_count
        float engagement_rate
        float engagement_score_alt
        float engagement_score_log
        float age_weight
    }

    AUDIO_FILE {
        string url FK
        string wav_path
        string mp3_path
        integer target_bpm
        float bpm_librosa
        float bpm_essentia
    }

    FEATURES {
        string url FK
        float tempo_confidence
        integer beats_count
        float onset_rate
        float harmonic_percussive_ratio
        integer key
        integer scale
        float key_strength
        text timbral_mfcc_mean
        float spectral_centroid_avg
        text deep_embeds_vggish
    }
```

> **Nota:** No banco SQLite atual (`playlist.db`), estas entidades estão desnormalizadas na tabela única `track_info`. O diagrama acima representa o modelo lógico implícito.
