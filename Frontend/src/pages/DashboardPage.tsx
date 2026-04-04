import { useState, useEffect } from 'react'
import { Segmented, Tag, Table, Button, Typography, Alert, Badge, Spin, Dropdown } from 'antd'
import { FilterOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined, MessageOutlined, DatabaseOutlined, LogoutOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { isStaff, isGuest, getPendingSources, getTopics } from '../api'
import logoSrc from '/logo.png'
import ThemeToggle from '../components/ThemeToggle'
import styles from './DashboardPage.module.css'

interface DashboardPageProps {
  isDark: boolean
  onToggleTheme: () => void
  onSelectTopic: (topicId: number) => void
  onOpenSources?: () => void
  onLogout: () => void
}

interface Problem {
  key: number
  rank: number
  title: string
  industry: string
  location: string
  dynamic: 'up' | 'down' | 'stable'
  mentions: number
}

const INDUSTRY_COLORS: Record<string, string> = {
  'ЖКХ': 'orange',
  'Дороги и транспорт': 'blue',
  'Транспорт': 'blue',
  'Здравоохранение': 'red',
  'Образование': 'green',
  'Экология и ЧС': 'cyan',
  'Экология': 'cyan',
  'Экономика и промышленность': 'purple',
  'Экономика': 'purple',
  'Безопасность и правопорядок': 'volcano',
  'Социальная защита': 'gold',
  'Культура и спорт': 'lime',
  'Цифровизация и связь': 'geekblue',
  'Сельское хозяйство': 'green',
  'Строительство и земля': 'orange',
  'Религия и духовная жизнь': 'magenta',
}

const getIndustryColor = (industry: string) => INDUSTRY_COLORS[industry] || 'default'

const DynamicIndicator = ({ type }: { type: Problem['dynamic'] }) => {
  if (type === 'up') return <ArrowUpOutlined className={styles.dynamicUp} />
  if (type === 'down') return <ArrowDownOutlined className={styles.dynamicDown} />
  return <MinusOutlined className={styles.dynamicStable} />
}

const DashboardPage = ({ isDark, onToggleTheme, onSelectTopic, onOpenSources, onLogout }: DashboardPageProps) => {
  const [period, setPeriod] = useState<string>('Неделя')
  const [industry, setIndustry] = useState<string | null>(null)
  const [pendingCount, setPendingCount] = useState(0)
  const [topics, setTopics] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState('')
  const themeClass = isDark ? styles.dark : styles.light
  const staff = isStaff()

  const PERIOD_MAP: Record<string, string> = {
    'Сегодня': 'today',
    'Неделя': 'week',
    'Месяц': 'month',
  }

  const ALL_INDUSTRIES = [
    'ЖКХ', 'Дороги и транспорт', 'Здравоохранение', 'Образование',
    'Экология и ЧС', 'Экономика и промышленность', 'Безопасность и правопорядок',
    'Социальная защита', 'Культура и спорт', 'Цифровизация и связь',
    'Сельское хозяйство', 'Строительство и земля', 'Религия и духовная жизнь',
  ]

  // Загрузить топики
  useEffect(() => {
    const fetchTopics = async () => {
      setLoading(true)
      try {
        const data = await getTopics(PERIOD_MAP[period], industry || undefined)
        setTopics(data)
        setLastUpdate(new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }))
      } catch {
        setTopics([])
      } finally {
        setLoading(false)
      }
    }
    fetchTopics()

    const interval = setInterval(fetchTopics, 300000)
    return () => clearInterval(interval)
  }, [period, industry])

  // Загрузить количество pending источников
  useEffect(() => {
    if (staff) {
      getPendingSources()
        .then((data: unknown[]) => setPendingCount(data.length))
        .catch(() => {})
    }
  }, [staff])

  const columns: ColumnsType<Problem> = [
    {
      title: 'РАНГ',
      dataIndex: 'rank',
      key: 'rank',
      width: 70,
      render: (rank: number) => <span className={styles.rank}>{rank}</span>,
    },
    {
      title: 'ЗАГОЛОВОК',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      ellipsis: true,
      render: (title: string) => <span className={styles.titleText}>{title}</span>,
    },
    {
      title: 'ОТРАСЛЬ',
      dataIndex: 'industry',
      key: 'industry',
      width: 150,
      render: (industry: string) => (
        <Tag color={getIndustryColor(industry)} className={styles.industryTag}>
          {industry}
        </Tag>
      ),
    },
    {
      title: 'ГЕОЛОКАЦИЯ',
      dataIndex: 'location',
      key: 'location',
      width: 180,
      render: (loc: string) => <span className={styles.locationText}>{loc || '—'}</span>,
    },
    {
      title: 'ДИНАМИКА',
      dataIndex: 'dynamic',
      key: 'dynamic',
      width: 100,
      align: 'center',
      render: (d: Problem['dynamic']) => <DynamicIndicator type={d} />,
    },
    {
      title: 'УПОМИНАНИЯ',
      dataIndex: 'mentions',
      key: 'mentions',
      width: 130,
      render: (count: number) => (
        <span className={styles.mentions}>
          <MessageOutlined /> {count}
        </span>
      ),
    },
  ]

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

        {/* Toolbar */}
        <div className={styles.toolbar}>
          {staff && onOpenSources && (
            <Badge count={pendingCount} size="small" offset={[-4, 0]}>
              <button className={styles.toolbarBtn} onClick={onOpenSources}>
                <DatabaseOutlined />
                <span>Источники</span>
              </button>
            </Badge>
          )}
          <button className={styles.toolbarBtn} onClick={onLogout}>
            <LogoutOutlined />
            <span>Выход</span>
          </button>
        </div>

        {isGuest() && (
          <Alert
            message="Вы в гостевом режиме. Доступен только просмотр."
            type="info"
            showIcon
            style={{ marginBottom: 16, borderRadius: 12 }}
          />
        )}

        <div className={styles.glassCard}>
          {/* Title section */}
          <div className={styles.titleSection}>
            <div>
              <Typography.Title level={3} className={styles.pageTitle}>
                Топ-10
              </Typography.Title>
              <span className={styles.subtitle}>Ростовская область</span>
            </div>
            <span className={styles.updateTime}>
              {lastUpdate ? `Обновлено в ${lastUpdate}` : 'Загрузка...'}
            </span>
          </div>

          {/* Controls */}
          <div className={styles.controls}>
            <Segmented
              options={['Сегодня', 'Неделя', 'Месяц']}
              value={period}
              onChange={(val) => setPeriod(val as string)}
              className={styles.segmented}
            />
            <Dropdown
              menu={{
                items: [
                  { key: 'all', label: 'Все отрасли' },
                  { type: 'divider' },
                  ...ALL_INDUSTRIES.map(ind => ({
                    key: ind,
                    label: (
                      <span>
                        <Tag color={getIndustryColor(ind)} style={{ marginRight: 8 }}>{ind}</Tag>
                      </span>
                    ),
                  })),
                ],
                onClick: ({ key }) => setIndustry(key === 'all' ? null : key),
                selectedKeys: industry ? [industry] : ['all'],
              }}
              trigger={['click']}
            >
              <Button
                icon={<FilterOutlined />}
                className={styles.filterBtn}
              >
                {industry || 'Фильтры'}
                {industry && (
                  <CloseCircleOutlined
                    style={{ marginLeft: 6, fontSize: 12 }}
                    onClick={(e) => { e.stopPropagation(); setIndustry(null) }}
                  />
                )}
              </Button>
            </Dropdown>
          </div>

          {/* Table */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <p style={{ marginTop: 16, opacity: 0.6 }}>Загрузка аналитики...</p>
            </div>
          ) : topics.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', opacity: 0.6 }}>
              <p>Пока нет данных для анализа.</p>
              <p>Добавьте источники и дождитесь сбора сообщений.</p>
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={topics}
              pagination={false}
              scroll={{ x: 880 }}
              className={styles.table}
              size="middle"
              onRow={(record) => ({
                onClick: () => onSelectTopic(record.key),
                style: { cursor: 'pointer' },
              })}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
