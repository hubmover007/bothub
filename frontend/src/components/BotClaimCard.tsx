import React from 'react';
import { Bot } from '../types/bot';

interface BotClaimCardProps {
  bot: Bot;
  onClaim?: (botId: string, claimType: 'owner' | 'hire' | 'share') => void;
  onUploadAvatar?: (botId: string, file: File) => void;
}

export function BotClaimCard({ bot, onClaim, onUploadAvatar }: BotClaimCardProps) {
  const [showClaimMenu, setShowClaimMenu] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleAvatarClick = () => {
    if (bot.is_owner) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUploadAvatar) {
      onUploadAvatar(bot.bot_id, file);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-gray-500';
      case 'busy':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      case 'unclaimed':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      online: '在线',
      offline: '离线',
      busy: '忙碌',
      error: '错误',
      unclaimed: '未认领',
      claimed: '已认领',
    };
    return statusMap[status] || status;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div
          className={`relative ${bot.is_owner ? 'cursor-pointer group' : ''}`}
          onClick={handleAvatarClick}
        >
          {bot.avatar_url ? (
            <img
              src={bot.avatar_url}
              alt={bot.bot_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
              {bot.bot_name[0]}
            </div>
          )}
          
          {/* Upload overlay for owner */}
          {bot.is_owner && (
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 rounded-full flex items-center justify-center transition-all">
              <span className="text-white text-xs opacity-0 group-hover:opacity-100">
                上传
              </span>
            </div>
          )}
          
          {/* Status indicator */}
          <div
            className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-white ${getStatusColor(
              bot.status
            )}`}
          />
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>

        {/* Bot Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-semibold text-gray-900">{bot.bot_name}</h3>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                bot.status === 'unclaimed'
                  ? 'bg-blue-100 text-blue-800'
                  : bot.status === 'online'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {getStatusText(bot.status)}
            </span>
          </div>

          <p className="text-sm text-gray-500 mt-1">ID: {bot.bot_id}</p>

          {bot.description && (
            <p className="text-gray-700 mt-2 text-sm">{bot.description}</p>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        {bot.version && (
          <div className="flex items-center gap-1">
            <span className="font-medium">版本:</span>
            <span>{bot.version}</span>
          </div>
        )}
        
        {bot.feishu_app_id && (
          <div className="flex items-center gap-1">
            <span className="font-medium">飞书:</span>
            <span className="text-blue-600">已绑定</span>
          </div>
        )}

        {bot.last_heartbeat_at && (
          <div className="flex items-center gap-1">
            <span className="font-medium">最后心跳:</span>
            <span>{new Date(bot.last_heartbeat_at).toLocaleString('zh-CN')}</span>
          </div>
        )}
      </div>

      {/* Capabilities */}
      {bot.capabilities && Object.keys(bot.capabilities).length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">能力:</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(bot.capabilities).map(([key, value]) =>
              value ? (
                <span
                  key={key}
                  className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
                >
                  {key}
                </span>
              ) : null
            )}
          </div>
        </div>
      )}

      {/* Owner Info */}
      {bot.owner && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2">
            {bot.owner.avatar_url && (
              <img
                src={bot.owner.avatar_url}
                alt={bot.owner.name}
                className="w-6 h-6 rounded-full"
              />
            )}
            <span className="text-sm text-gray-600">
              所有者: <span className="font-medium">{bot.owner.name}</span>
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200 flex gap-2">
        {bot.can_claim && (
          <div className="relative">
            <button
              onClick={() => setShowClaimMenu(!showClaimMenu)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              {bot.status === 'unclaimed' ? '认领' : '请求访问'}
            </button>

            {showClaimMenu && (
              <div className="absolute top-full mt-2 left-0 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10 w-32">
                {bot.status === 'unclaimed' && (
                  <button
                    onClick={() => {
                      onClaim?.(bot.bot_id, 'owner');
                      setShowClaimMenu(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
                  >
                    所有者认领
                  </button>
                )}
                
                {bot.status !== 'unclaimed' && (
                  <>
                    <button
                      onClick={() => {
                        onClaim?.(bot.bot_id, 'hire');
                        setShowClaimMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
                    >
                      雇佣
                    </button>
                    <button
                      onClick={() => {
                        onClaim?.(bot.bot_id, 'share');
                        setShowClaimMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
                    >
                      分享
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => window.location.href = `/bots/${bot.bot_id}`}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors text-sm font-medium"
        >
          查看详情
        </button>
      </div>

      {/* Claim time */}
      {bot.claimed_at && (
        <p className="mt-3 text-xs text-gray-500">
          认领于 {new Date(bot.claimed_at).toLocaleString('zh-CN')}
        </p>
      )}
    </div>
  );
}
