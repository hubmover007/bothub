import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import apiClient from '../api/client';
import type { Bot } from '../types/bot';
import BotCard from '../components/BotCard';

export default function BotHall() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: bots, isLoading, error } = useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await apiClient.get<Bot[]>('/api/v1/bots');
      return response.data;
    },
  });

  const filteredBots = bots?.filter((bot) => {
    const matchesSearch = bot.bot_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      bot.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || bot.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">机器人大厅</h1>
          <p className="text-muted-foreground">浏览和管理所有注册的机器人</p>
        </div>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
          + 注册新机器人
        </button>
      </div>

      <div className="flex gap-4">
        <input
          type="text"
          placeholder="搜索机器人..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">所有状态</option>
          <option value="online">在线</option>
          <option value="offline">离线</option>
          <option value="error">错误</option>
        </select>
      </div>

      {isLoading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">加载中...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-destructive">加载失败: {(error as Error).message}</p>
        </div>
      )}

      {filteredBots && filteredBots.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">暂无机器人</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredBots?.map((bot) => (
          <BotCard key={bot.id} bot={bot} />
        ))}
      </div>
    </div>
  );
}
