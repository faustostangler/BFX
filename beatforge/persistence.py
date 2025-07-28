# persistence.py

import sqlite3
import json
from typing import List, Dict, Set
from beatforge.track import TrackDTO


# Name of the table used for storing track information in the database
TABLE_NAME = "track_info"

def init_db(db_path: str):
    """
    Initializes the database at the specified path by ensuring the required schema exists.

    Args:
        db_path (str): The file path to the database.

    Raises:
        Any exception raised by ensure_schema if schema creation fails.
    """
    ensure_schema(db_path)

def ensure_schema(db_path: str):
    """
    Ensures that the database schema exists at the specified path.

    This function connects to the SQLite database at `db_path` and creates a table
    (named by the global `TABLE_NAME`) if it does not already exist. The table is
    designed to store metadata and analysis results for audio files, including
    paths, BPM information, engagement metrics, audio features, and deep embeddings.

    Args:
        db_path (str): The file path to the SQLite database.

    Raises:
        sqlite3.Error: If an error occurs while connecting to the database or executing SQL.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                url TEXT PRIMARY KEY,
                wav_path TEXT,
                bpm_librosa REAL,
                target_bpm INTEGER,
                mp3_path TEXT,

                age_weight REAL,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                engagement_rate REAL,
                engagement_score_alt REAL,
                engagement_score_log REAL,
                title TEXT,
                artist TEXT,
                album TEXT,
                safe_title TEXT,

                bpm_essentia REAL,
                tempo_confidence REAL,
                beats_count INTEGER,
                onset_rate REAL,
                harmonic_percussive_ratio REAL,
                key INTEGER,
                scale INTEGER,
                key_strength REAL,

                timbral_mfcc_mean REAL,
                timbral_mfcc_std REAL,

                spectral_centroid_avg REAL,
                spectral_zcr_avg REAL,
                spectral_rolloff_avg REAL,
                spectral_flatness_avg REAL,
                spectral_flux_avg REAL,
                spectral_contrast_mean REAL,
                spectral_dissonance_avg REAL,

                chroma_chroma_mean REAL,
                chroma_chroma_std REAL,

                dynamics_energy_avg REAL,
                dynamics_rms_avg REAL,
                dynamics_loudness_avg REAL,
                dynamics_crest_factor REAL,

                deep_embeds_vggish TEXT -- JSON-encoded list
            )
        """)
        conn.commit()

def save_track_list(tracks: List[TrackDTO], db_path: str):
    """
    Saves a list of TrackDTO objects to the specified SQLite database.

    Each track in the list is inserted or replaced into the table defined by TABLE_NAME.
    The function serializes the 'deep_embeds_vggish' attribute to JSON before storing.

    Args:
        tracks (List[TrackDTO]): A list of TrackDTO objects to be saved.
        db_path (str): Path to the SQLite database file.

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the operation.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for t in tracks:
            params = {
                **t.__dict__,
                "timbral_mfcc_mean": json.dumps(t.timbral_mfcc_mean),
                "timbral_mfcc_std": json.dumps(t.timbral_mfcc_std),
                "spectral_contrast_mean": json.dumps(t.spectral_contrast_mean),
                "chroma_chroma_mean": json.dumps(t.chroma_chroma_mean),
                "chroma_chroma_std": json.dumps(t.chroma_chroma_std),
                "deep_embeds_vggish": json.dumps(t.deep_embeds_vggish),
            }
            cursor.execute(f"""
                INSERT OR REPLACE INTO {TABLE_NAME} VALUES (
                    :url, :wav_path, :bpm_librosa, :target_bpm, :mp3_path,
                    :age_weight, :view_count, :like_count, :comment_count, :engagement_rate,
                    :engagement_score_alt, :engagement_score_log, :title, :artist, :album, :safe_title,
                    :bpm_essentia, :tempo_confidence, :beats_count, :onset_rate, :harmonic_percussive_ratio,
                    :key, :scale, :key_strength,
                    :timbral_mfcc_mean, :timbral_mfcc_std,
                    :spectral_centroid_avg, :spectral_zcr_avg, :spectral_rolloff_avg, :spectral_flatness_avg,
                    :spectral_flux_avg, :spectral_contrast_mean, :spectral_dissonance_avg,
                    :chroma_chroma_mean, :chroma_chroma_std,
                    :dynamics_energy_avg, :dynamics_rms_avg, :dynamics_loudness_avg, :dynamics_crest_factor,
                    :deep_embeds_vggish
                )
            """, params)
        conn.commit()

def load_all_tracks(db_path: str) -> Dict[str, TrackDTO]:
    """
    Loads all tracks from the specified SQLite database and returns them as a dictionary of TrackDTO objects.

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        Dict[str, TrackDTO]: A dictionary mapping track URLs to their corresponding TrackDTO objects.

    Raises:
        sqlite3.DatabaseError: If there is an error connecting to or querying the database.
        json.JSONDecodeError: If the 'deep_embeds_vggish' field contains invalid JSON.

    Notes:
        - Assumes the existence of a TABLE_NAME constant and a TrackDTO class.
        - The 'deep_embeds_vggish' field is expected to be a JSON-encoded string or None.
    """
    ensure_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        columns = [desc[0] for desc in cursor.description]
        result = {}
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            for k in [
                "timbral_mfcc_mean", "timbral_mfcc_std",
                "spectral_contrast_mean", "chroma_chroma_mean",
                "chroma_chroma_std", "deep_embeds_vggish"
            ]:
                if data.get(k):
                    try:
                        data[k] = json.loads(data[k])
                    except json.JSONDecodeError:
                        data[k] = []
                else:
                    data[k] = []
            result[data["url"]] = TrackDTO(**data)
        return result

def get_processed_urls(db_path: str) -> Set[str]:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT url FROM track_info WHERE bpm_librosa IS NOT NULL OR bpm_essentia IS NOT NULL;")
    urls = {row[0] for row in cur.fetchall()}
    conn.close()
    return urls