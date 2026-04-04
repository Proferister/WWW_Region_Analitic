import { useState, useEffect, useCallback } from 'react'
import { Avatar, Button, Tag, Popconfirm, Spin, Collapse, Input, message } from 'antd'
import {
  DeleteOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  ClockCircleOutlined,
  QuestionCircleOutlined,
  CopyOutlined,
  LinkOutlined,
  SendOutlined,
  CommentOutlined,
  WifiOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import {
  getSources,
  getPendingSources,
  approveSource,
  rejectSource,
  deleteSource,
  addRssSource,
  isStaff,
} from '../api'
import logoSrc from '/logo.png'
import ThemeToggle from '../components/ThemeToggle'
import styles from './SourcesPage.module.css'

interface SourcesPageProps {
  isDark: boolean
  onToggleTheme: () => void
  onBack: () => void
}

interface Source {
  id: number
  platform: string
  name: string
  description: string | null
  source_id: string
  source_url: string | null
  avatar_url: string | null
  status: 'pending' | 'approved' | 'rejected'
  is_active: boolean
  created_at: string
}

const TG_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || '@MADRIGAL_BOT'
const TG_BOT_URL = import.meta.env.VITE_TELEGRAM_BOT_URL || 'https://t.me/madrigal_bot'
const MAX_BOT_USERNAME = import.meta.env.VITE_MAX_BOT_USERNAME || '@MADRIGAL_BOT'
const MAX_BOT_URL = import.meta.env.VITE_MAX_BOT_URL || 'https://max.ru/madrigal_bot'

const PLATFORM_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  max: { label: 'MAX', color: 'purple', icon: <CommentOutlined /> },
  telegram: { label: 'TG', color: 'blue', icon: <SendOutlined /> },
  rss: { label: 'RSS', color: 'orange', icon: <WifiOutlined /> },
}

function platformBadge(platform: string) {
  return PLATFORM_CONFIG[platform] || { label: platform.toUpperCase(), color: 'gray', icon: null }
}

function statusBadge(status: string) {
  switch (status) {
    case 'approved': return { color: 'green', text: 'Подключён' }
    case 'pending': return { color: 'orange', text: 'Ожидает' }
    case 'rejected': return { color: 'red', text: 'Отклонён' }
    default: return { color: 'gray', text: status }
  }
}

function SourceAvatar({ source }: { source: Source }) {
  const pConfig = platformBadge(source.platform)
  if (source.avatar_url) {
    return <Avatar src={source.avatar_url} size={36} className={styles.sourceAvatar} />
  }
  return (
    <Avatar size={36} className={styles.sourceAvatar} style={{ background: 'rgba(139,92,246,0.15)' }}>
      {pConfig.icon}
    </Avatar>
  )
}

const SourcesPage = ({ isDark, onToggleTheme, onBack }: SourcesPageProps) => {
  const [approved, setApproved] = useState<Source[]>([])
  const [pending, setPending] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [rssUrl, setRssUrl] = useState('')
  const [rssLoading, setRssLoading] = useState(false)
  const themeClass = isDark ? styles.dark : styles.light
  const staff = isStaff()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [sourcesRes, pendingRes] = await Promise.all([
        getSources(),
        staff ? getPendingSources() : Promise.resolve([]),
      ])
      setApproved(
        (sourcesRes as Source[]).filter((s) => s.status === 'approved')
      )
      setPending(pendingRes as Source[])
    } catch {
      message.error('Не удалось загрузить источники')
    } finally {
      setLoading(false)
    }
  }, [staff])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleAddRss = async () => {
    if (!rssUrl.trim()) return
    setRssLoading(true)
    try {
      await addRssSource(rssUrl.trim())
      message.success('RSS-источник добавлен')
      setRssUrl('')
      loadData()
    } catch (err: any) {
      message.error(err?.detail || 'Ошибка добавления RSS')
    } finally {
      setRssLoading(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('Скопировано!')
  }

  const handleApprove = async (id: number) => {
    try {
      await approveSource(id)
      message.success('Источник подключён')
      loadData()
    } catch {
      message.error('Ошибка подтверждения')
    }
  }

  const handleReject = async (id: number) => {
    try {
      await rejectSource(id)
      message.success('Источник отклонён')
      loadData()
    } catch {
      message.error('Ошибка отклонения')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteSource(id)
      message.success('Источник удалён')
      loadData()
    } catch {
      message.error('Ошибка удаления')
    }
  }

  const showInstructions = approved.length === 0 && pending.length === 0

  return (
    <div className={`${styles.wrapper} ${themeClass}`}>
      <div className={styles.bgShape1} />
      <div className={styles.bgShape2} />
      <div className={styles.bgShape3} />

      <div className={styles.themeToggle}>
        <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
      </div>

      <div className={styles.container}>
        <div className={styles.header}>
          <img src={logoSrc} alt="WHITEA" className={styles.logo} />
          <h2 className={styles.brandTitle}>WHITEA</h2>
        </div>

        <div className={styles.navRow}>
          <button className={styles.backBtn} onClick={onBack}>
            <ArrowLeftOutlined />
          </button>
          <h1 className={styles.pageTitle}>Источники</h1>
          <span className={styles.countBadge}>{approved.length}</span>
        </div>

        {loading ? (
          <div className={styles.spinWrap}>
            <Spin size="large" />
          </div>
        ) : (
          <>
            {/* Instructions */}
            <Collapse
              ghost
              defaultActiveKey={showInstructions ? ['max', 'tg'] : []}
              className={styles.guideCollapse}
              items={[
                {
                  key: 'max',
                  label: (
                    <span className={styles.guideLabel}>
                      <CommentOutlined /> Подключить MAX
                    </span>
                  ),
                  children: (
                    <div className={styles.guideContent}>
                      <div className={styles.stepsList}>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>1</span>
                          <span className={styles.stepText}>
                            Скопируйте бота: <strong>{MAX_BOT_USERNAME}</strong>
                          </span>
                          <button className={styles.stepAction} onClick={() => handleCopy(MAX_BOT_USERNAME)}>
                            <CopyOutlined /> Скопировать
                          </button>
                        </div>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>2</span>
                          <span className={styles.stepText}>Добавьте бота в группу MAX</span>
                          <button className={styles.stepAction} onClick={() => window.open(MAX_BOT_URL, '_blank')}>
                            <LinkOutlined /> Открыть
                          </button>
                        </div>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>3</span>
                          <span className={styles.stepText}>Выдайте права на чтение — бот появится в списке ниже</span>
                        </div>
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'tg',
                  label: (
                    <span className={styles.guideLabel}>
                      <SendOutlined /> Подключить Telegram
                    </span>
                  ),
                  children: (
                    <div className={styles.guideContent}>
                      <div className={styles.stepsList}>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>1</span>
                          <span className={styles.stepText}>
                            Скопируйте бота: <strong>{TG_BOT_USERNAME}</strong>
                          </span>
                          <button className={styles.stepAction} onClick={() => handleCopy(TG_BOT_USERNAME)}>
                            <CopyOutlined /> Скопировать
                          </button>
                        </div>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>2</span>
                          <span className={styles.stepText}>Добавьте бота в канал или группу Telegram</span>
                          <button className={styles.stepAction} onClick={() => window.open(TG_BOT_URL, '_blank')}>
                            <LinkOutlined /> Открыть
                          </button>
                        </div>
                        <div className={styles.stepRow}>
                          <span className={styles.stepNumber}>3</span>
                          <span className={styles.stepText}>Выдайте права на чтение сообщений — бот появится в списке ниже</span>
                        </div>
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'rss',
                  label: (
                    <span className={styles.guideLabel}>
                      <WifiOutlined /> Добавить RSS
                    </span>
                  ),
                  children: (
                    <div className={styles.guideContent}>
                      <p className={styles.rssHint}>Вставьте URL RSS-ленты — источник подключится автоматически</p>
                      <div className={styles.rssForm}>
                        <Input
                          value={rssUrl}
                          onChange={(e) => setRssUrl(e.target.value)}
                          placeholder="https://example.com/rss"
                          size="large"
                          className={styles.rssInput}
                          onPressEnter={handleAddRss}
                        />
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={handleAddRss}
                          loading={rssLoading}
                          disabled={!rssUrl.trim()}
                        >
                          Добавить
                        </Button>
                      </div>
                    </div>
                  ),
                },
              ]}
            />

            {/* Pending block — staff only, exclude RSS */}
            {(() => {
              const pendingNonRss = pending.filter((s) => s.platform !== 'rss')
              return staff && pendingNonRss.length > 0 && (
                <>
                  <h3 className={styles.sectionTitle}>
                    <ClockCircleOutlined /> Ожидают подтверждения
                    <span className={styles.sectionCount}>{pendingNonRss.length}</span>
                  </h3>
                  <div className={styles.sourcesList}>
                    {pendingNonRss.map((source) => (
                      <div key={source.id} className={styles.sourceCard}>
                        <div className={styles.sourceInfo}>
                          <SourceAvatar source={source} />
                          <Tag color={platformBadge(source.platform).color} className={styles.platformTag}>
                            {platformBadge(source.platform).label}
                          </Tag>
                          <div className={styles.sourceDetails}>
                            <span className={styles.sourceName}>{source.name}</span>
                            {source.description && (
                              <span className={styles.sourceDesc}>{source.description}</span>
                            )}
                          </div>
                        </div>
                        <div className={styles.sourceActions}>
                          <Button
                            type="primary"
                            size="small"
                            icon={<CheckOutlined />}
                            className={styles.approveBtn}
                            onClick={() => handleApprove(source.id)}
                          >
                            Подключить
                          </Button>
                          <Button
                            size="small"
                            danger
                            icon={<CloseOutlined />}
                            onClick={() => handleReject(source.id)}
                          >
                            Отклонить
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )
            })()}

            {/* Approved block */}
            <h3 className={styles.sectionTitle}>
              <CheckCircleOutlined /> Подключённые
              <span className={styles.sectionCount}>{approved.length}</span>
            </h3>
            <div className={styles.sourcesList}>
              {approved.map((source) => {
                const badge = statusBadge(source.status)
                return (
                  <div key={source.id} className={styles.sourceCard}>
                    <div className={styles.sourceInfo}>
                      <SourceAvatar source={source} />
                      <Tag color={platformBadge(source.platform).color} className={styles.platformTag}>
                        {platformBadge(source.platform).label}
                      </Tag>
                      <div className={styles.sourceDetails}>
                        <span className={styles.sourceName}>{source.name}</span>
                        {source.description && (
                          <span className={styles.sourceDesc}>{source.description}</span>
                        )}
                      </div>
                    </div>
                    <div className={styles.sourceActions}>
                      <Tag color={badge.color} className={styles.statusTag}>
                        {badge.text}
                      </Tag>
                      {staff && (
                        <Popconfirm
                          title="Удалить источник?"
                          description="Это действие нельзя отменить"
                          onConfirm={() => handleDelete(source.id)}
                          okText="Удалить"
                          cancelText="Отмена"
                          okButtonProps={{ danger: true }}
                        >
                          <button className={styles.deleteBtn}>
                            <DeleteOutlined />
                          </button>
                        </Popconfirm>
                      )}
                    </div>
                  </div>
                )
              })}

              {approved.length === 0 && (
                <p className={styles.emptyText}>
                  Нет подключённых источников. Добавьте бота — инструкция выше.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default SourcesPage
