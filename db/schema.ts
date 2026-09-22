import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

// Single-owner Spotify connection, short-lived OAuth attempts and bounded feed cache.
// Credential values are encrypted before reaching this table.
export const spotifyState = sqliteTable("spotify_state", {
  key: text("key").primaryKey(),
  value: text("value").notNull(),
  expiresAt: integer("expires_at").notNull().default(0),
});
