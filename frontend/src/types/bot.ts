export interface Bot {
  id: string;
  bot_id: string;
  bot_name: string;
  owner_id: string;
  description?: string;
  status: 'online' | 'offline' | 'error';
  capabilities: string[];
  endpoint?: string;
  version?: string;
  created_at: string;
  updated_at: string;
  last_heartbeat_at?: string;
}

export interface BotCreate {
  bot_id: string;
  bot_name: string;
  owner_id: string;
  description?: string;
  capabilities?: string[];
  endpoint?: string;
  version?: string;
}

export interface BotHeartbeat {
  bot_id: string;
  status: 'online' | 'offline' | 'error';
}
