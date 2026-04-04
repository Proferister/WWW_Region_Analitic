import { useState, useEffect } from 'react'
import { Button, Tag, Spin } from 'antd'
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  EnvironmentOutlined,
  FrownOutlined,
  LinkOutlined,
  FilePdfOutlined,
} from '@ant-design/icons'
import { Line } from '@ant-design/charts'
import { getTopicDetail, authFetch, isInsideMax, sendTopicPdf } from '../api'
import logoSrc from '/logo.png'
import ThemeToggle from '../components/ThemeToggle'
import styles from './TopicDetailPage.module.css'

interface TopicDetailPageProps {
  isDark: boolean
  onToggleTheme: () => void
  topicId: number
  onBack: () => void
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

interface TopicData {
  id: number
  rank: number
  title: string
  industry: string
  location: string
  period: string
  summary: string
  stats: {
    mentionsGrowth: string
    locations: number
    negativePct: number
  }
  chartData: { day: string; mentions: number }[]
  peakLabel: string
  reliability: {
    status: 'confirmed' | 'suspicious' | 'unclear'
    confirmedSources: number
    filteredBots: number
  }
  sources: {
    platform: string
    channel: string
    message: string
    date: string
    link: string
  }[]
  keywords: string[]
  dynamic: string
  mentions: number
}

const TopicDetailPage = ({ isDark, onToggleTheme, topicId, onBack }: TopicDetailPageProps) => {
  const themeClass = isDark ? styles.dark : styles.light
  const [data, setData] = useState<TopicData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTopic = async () => {
      setLoading(true)
      try {
        const result = await getTopicDetail(topicId)
        setData(result)
      } catch {
        setData(null)
      } finally {
        setLoading(false)
      }
    }
    fetchTopic()
  }, [topicId])

  if (loading) {
    return (
      <div className={`${styles.wrapper} ${themeClass}`}>
        <div style={{ textAlign: 'center', padding: '120px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16, opacity: 0.6 }}>Загрузка...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={`${styles.wrapper} ${themeClass}`}>
        <div className={styles.container}>
          <button className={styles.backBtn} onClick={onBack}>
            <ArrowLeftOutlined /> Назад
          </button>
          <p style={{ textAlign: 'center', padding: '60px 0', opacity: 0.6 }}>
            Тема не найдена
          </p>
        </div>
      </div>
    )
  }

  const labelColor = isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.6)'
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.1)'
  const lineColor = isDark ? '#a78bfa' : '#7c3aed'

  const chartConfig = {
    data: data.chartData || [],
    xField: 'day',
    yField: 'mentions',
    smooth: true,
    style: {
      stroke: lineColor,
      lineWidth: 2,
    },
    point: {
      shapeField: 'circle',
      sizeField: 3,
      style: { fill: lineColor },
    },
    axis: {
      x: {
        label: { style: { fill: labelColor, fontSize: 11 } },
        line: false,
        tick: false,
      },
      y: {
        label: { style: { fill: labelColor, fontSize: 11 } },
        grid: true,
        gridStroke: gridColor,
      },
    },
    autoFit: true,
    height: 200,
    padding: 'auto' as const,
  }

  const reliabilityColor =
    data.reliability.status === 'confirmed' ? '#22c55e' :
    data.reliability.status === 'suspicious' ? '#eab308' : '#9ca3af'

  const reliabilityText =
    data.reliability.status === 'confirmed'
      ? `Достоверно — подтверждено из ${data.reliability.confirmedSources} источников`
      : data.reliability.status === 'suspicious'
        ? 'Нуждается в проверке — только 1 источник'
        : 'Нет подтверждённых источников'

  return (
    <div className={`${styles.wrapper} ${themeClass}`}>
      <div className={styles.bgShape1} />
      <div className={styles.bgShape2} />
      <div className={styles.bgShape3} />

      <div className={styles.themeToggle}>
        <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
      </div>

      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <img src={logoSrc} alt="WHITEA" className={styles.logo} />
          <h2 className={styles.brandTitle}>WHITEA</h2>
        </div>

        {/* Navigation + Title */}
        <div className={styles.navRow}>
          <button className={styles.backBtn} onClick={onBack}>
            <ArrowLeftOutlined />
          </button>
          <span className={styles.rankBadge}>#{data.rank} в топ-10</span>
        </div>

        <h1 className={styles.topicTitle}>{data.title}</h1>

        <div className={styles.metaRow}>
          <Tag color={getIndustryColor(data.industry)}>{data.industry}</Tag>
          {data.location && <span className={styles.metaText}>{data.location}</span>}
          {data.period && <span className={styles.metaText}>{data.period}</span>}
        </div>

        {/* Block 1: Сводка */}
        <div className={styles.glassCard}>
          <h3 className={styles.sectionTitle}>Сводка</h3>
          <p className={styles.summaryText}>{data.summary || 'Описание формируется...'}</p>
        </div>

        {/* Block 2: Почему в топе */}
        <h3 className={styles.sectionTitleOutside}>ПОЧЕМУ В ТОПЕ?</h3>
        <div className={styles.statsRow}>
          <div className={styles.statCard}>
            <BarChartOutlined className={styles.statIcon} />
            <span className={styles.statValue}>{data.stats.mentionsGrowth}</span>
          </div>
          <div className={styles.statCard}>
            <EnvironmentOutlined className={styles.statIcon} />
            <span className={styles.statValue}>{data.stats.locations} населённых пункта затронуты</span>
          </div>
          <div className={styles.statCard}>
            <FrownOutlined className={styles.statIcon} />
            <span className={styles.statValue}>{data.stats.negativePct}% негативных сообщений</span>
          </div>
        </div>

        {/* Block 3: Динамика */}
        {data.chartData && data.chartData.length > 0 && (
          <div className={styles.glassCard}>
            <div className={styles.chartContainer}>
              <Line {...chartConfig} />
            </div>
            <p className={styles.chartCaption}>
              ось X — дни, ось Y — количество упоминаний
            </p>
            {data.peakLabel && <p className={styles.chartPeak}>{data.peakLabel}</p>}
          </div>
        )}

        {/* Keywords */}
        {data.keywords && data.keywords.length > 0 && (
          <div className={styles.glassCard}>
            <h3 className={styles.sectionTitle}>Ключевые слова</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {data.keywords.map((kw, i) => (
                <Tag key={i} style={{ borderRadius: 12 }}>{kw}</Tag>
              ))}
            </div>
          </div>
        )}

        {/* Block 4: Достоверность */}
        <div className={styles.glassCard}>
          <h3 className={styles.sectionTitle}>Проверка достоверности</h3>
          <div className={styles.reliabilityRow}>
            <span className={styles.reliabilityDot} style={{ background: reliabilityColor }} />
            <span className={styles.reliabilityText}>{reliabilityText}</span>
          </div>
          {data.reliability.filteredBots > 0 && (
            <p className={styles.filteredText}>
              Отфильтровано {data.reliability.filteredBots} ботовых публикаций
            </p>
          )}
        </div>

        {/* Block 5: PDF-отчёт */}
        <Button
          type="primary"
          block
          icon={<FilePdfOutlined />}
          className={styles.glassButton}
          onClick={async () => {
            if (isInsideMax()) {
              // В MAX — отправить через бота
              try {
                await sendTopicPdf(topicId)
                alert('Отчёт отправлен вам в чат с ботом')
              } catch {
                alert('Не удалось отправить отчёт')
              }
            } else {
              // В браузере — скачать файл
              try {
                const token = localStorage.getItem('token')
                const API_URL = import.meta.env.VITE_API_URL || 'https://whitea.ru/api'
                const res = await fetch(`${API_URL}/dashboard/topics/${topicId}/pdf`, {
                  headers: { 'Authorization': `Bearer ${token}` },
                })
                if (res.ok) {
                  const blob = await res.blob()
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `report_topic_${topicId}.pdf`
                  a.click()
                  URL.revokeObjectURL(url)
                }
              } catch {
                // ошибка скачивания
              }
            }
          }}
        >
          {isInsideMax() ? 'Отправить PDF в чат' : 'Скачать PDF-отчёт'}
        </Button>

        {/* Block 6: Источники */}
        {data.sources && data.sources.length > 0 && (
          <>
            <h3 className={styles.sectionTitleOutside}>ИСТОЧНИКИ ({data.sources.length})</h3>
            <div className={styles.glassCard}>
              <div className={styles.sourcesList}>
                {data.sources.map((src, i) => (
                  <div key={i} className={styles.sourceItem}>
                    <div className={styles.sourceHeader}>
                      <Tag
                        color={src.platform === 'TG' ? 'blue' : src.platform === 'MAX' ? 'purple' : 'cyan'}
                        className={styles.platformTag}
                      >
                        {src.platform}
                      </Tag>
                      <span className={styles.sourceChannel}>{src.channel}</span>
                      <span className={styles.sourceDate}>{src.date}</span>
                    </div>
                    <p className={styles.sourceMessage}>{src.message}</p>
                    {src.link && src.link !== '#' && (
                      <a href={src.link} target="_blank" rel="noopener noreferrer" className={styles.sourceLink}>
                        <LinkOutlined /> Открыть
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default TopicDetailPage
