CREATE TABLE `spotify_state` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL,
	`expires_at` integer DEFAULT 0 NOT NULL
);
