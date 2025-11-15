import initSqlJs, { Database } from 'sql.js';

let db: Database | null = null;

export interface ReadingData {
  RPM: number;
  SPEED: number;
  ENGINE_LOAD: number;
  timestamp: string;
}

export async function initDatabase(): Promise<void> {
  try {
    const SQL = await initSqlJs({
      locateFile: (file) => `https://sql.js.org/dist/${file}`,
    });

    const response = await fetch('/auto_data1.db');
    const buffer = await response.arrayBuffer();
    db = new SQL.Database(new Uint8Array(buffer));
  } catch (error) {
    console.error('Failed to initialize database:', error);
    throw error;
  }
}

export async function getLatestReading(): Promise<ReadingData | null> {
  if (!db) {
    await initDatabase();
  }

  try {
    // Re-fetch the database file to get latest data
    const response = await fetch('/auto_data1.db?t=' + Date.now());
    const buffer = await response.arrayBuffer();
    const SQL = await initSqlJs({
      locateFile: (file) => `https://sql.js.org/dist/${file}`,
    });
    db = new SQL.Database(new Uint8Array(buffer));

    const result = db.exec(
      'SELECT RPM, SPEED, ENGINE_LOAD, timestamp FROM readings ORDER BY timestamp DESC LIMIT 1'
    );

    if (result.length > 0 && result[0].values.length > 0) {
      const row = result[0].values[0];
      return {
        RPM: (row[0] as number) || 0,
        SPEED: (row[1] as number) || 0,
        ENGINE_LOAD: (row[2] as number) || 0,
        timestamp: (row[3] as string) || '',
      };
    }

    return null;
  } catch (error) {
    console.error('Failed to fetch latest reading:', error);
    return null;
  }
}