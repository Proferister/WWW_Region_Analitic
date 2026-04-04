import { useState, useEffect, useCallback, useRef } from 'react'
import { Button, Form, Input, Typography, message } from 'antd'
import { MailOutlined } from '@ant-design/icons'
import { requestOtp, verifyOtp, guestLogin, isInsideMax } from '../api'
import logoSrc from '/logo.png'
import ThemeToggle from '../components/ThemeToggle'
import styles from './LoginPage.module.css'

interface LoginPageProps {
  isDark: boolean
  onToggleTheme: () => void
  onSuccess: () => void
}

const RESEND_SECONDS = 45
const CODE_LENGTH = 6
const CODE_EXPIRES_MINUTES = 5

const OtpInput = ({
  length,
  isDark,
  onChange,
}: {
  length: number
  isDark: boolean
  onChange: (code: string) => void
}) => {
  const [values, setValues] = useState<string[]>(Array(length).fill(''))
  const inputsRef = useRef<(HTMLInputElement | null)[]>([])

  const handleChange = (index: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const next = [...values]
    next[index] = val.slice(-1)
    setValues(next)
    onChange(next.join(''))
    if (val && index < length - 1) {
      inputsRef.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !values[index] && index > 0) {
      inputsRef.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length)
    const next = [...values]
    for (let i = 0; i < paste.length; i++) {
      next[i] = paste[i]
    }
    setValues(next)
    onChange(next.join(''))
    const focusIndex = Math.min(paste.length, length - 1)
    inputsRef.current[focusIndex]?.focus()
  }

  return (
    <div className={styles.otpRow}>
      {Array.from({ length }).map((_, i) => (
        <input
          key={i}
          ref={(el) => { inputsRef.current[i] = el }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={values[i]}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onPaste={i === 0 ? handlePaste : undefined}
          className={`${styles.otpCell} ${isDark ? styles.otpCellDark : styles.otpCellLight}`}
          autoFocus={i === 0}
        />
      ))}
    </div>
  )
}

const LoginPage = ({ isDark, onToggleTheme, onSuccess }: LoginPageProps) => {
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)
  const [emailForm] = Form.useForm()

  const startCountdown = useCallback(() => {
    setCountdown(RESEND_SECONDS)
  }, [])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown])

  const onEmailSubmit = async (values: { email: string }) => {
    setLoading(true)
    try {
      await requestOtp(values.email)
      setEmail(values.email)
      setStep('code')
      startCountdown()
    } catch (err: any) {
      const msg = err?.detail?.[0]?.msg || err?.detail || 'Ошибка отправки кода'
      message.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const onCodeSubmit = async () => {
    if (otp.length < CODE_LENGTH) return
    setLoading(true)
    try {
      await verifyOtp(email, otp)
      onSuccess()
    } catch (err: any) {
      const msg = err?.detail || 'Неверный или просроченный код'
      message.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const onGuestLogin = async () => {
    setLoading(true)
    try {
      await guestLogin()
      onSuccess()
    } catch (err: any) {
      const msg = err?.detail || 'Ошибка гостевого входа'
      message.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const onResend = async () => {
    if (countdown > 0) return
    try {
      await requestOtp(email)
      startCountdown()
      message.success('Код отправлен повторно')
    } catch {
      message.error('Не удалось отправить код')
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.wrapper} ${themeClass}`}>
      <div className={styles.bgShape1} />
      <div className={styles.bgShape2} />
      <div className={styles.bgShape3} />

      <div className={styles.themeToggle}>
        <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
      </div>

      <div className={styles.container}>
        <div className={styles.logoSection}>
          <img src={logoSrc} alt="WHITEA" className={styles.logo} />
          <Typography.Title
            level={2}
            style={{
              color: isDark ? '#fff' : '#1a1a2e',
              fontFamily: "'Unbounded', sans-serif",
              fontWeight: 800,
              letterSpacing: 4,
              margin: '0 0 0',
              fontSize: 28,
            }}
          >
            WHITEA
          </Typography.Title>
        </div>

        <div className={styles.glassCard}>
          {step === 'email' ? (
            <Form form={emailForm} layout="vertical" onFinish={onEmailSubmit} size="large">
              <Form.Item
                label={<span className={styles.label}>Email</span>}
                name="email"
                rules={[{ required: true, message: '' }]}
              >
                <Input
                  className={styles.glassInput}
                  placeholder="Email"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  className={styles.glassButton}
                  loading={loading}
                >
                  Войти
                </Button>
              </Form.Item>
            </Form>
          ) : (
            <div className={styles.codeStep}>
              <h3 className={styles.codeTitle}>Проверьте почту</h3>
              <p className={styles.codeSubtitle}>
                Мы отправили на почту код для входа
              </p>

              <div className={styles.emailDisplay}>
                <MailOutlined className={styles.emailIcon} />
                <span>{email}</span>
              </div>

              <OtpInput length={CODE_LENGTH} isDark={isDark} onChange={setOtp} />

              <Button
                type="primary"
                block
                className={styles.glassButton}
                onClick={onCodeSubmit}
                disabled={otp.length < CODE_LENGTH}
                loading={loading}
              >
                Войти
              </Button>

              <div className={styles.resendRow}>
                <span className={styles.resendText}>
                  Код действует <strong>{CODE_EXPIRES_MINUTES} минут</strong>
                </span>
                <span className={styles.resendDot}>·</span>
                {countdown > 0 ? (
                  <span className={styles.resendTimer}>
                    Повторно через {countdown} сек.
                  </span>
                ) : (
                  <button
                    type="button"
                    className={styles.resendLink}
                    onClick={onResend}
                  >
                    Отправить повторно
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {isInsideMax() && (
          <Button
            block
            className={styles.guestButton}
            onClick={onGuestLogin}
            loading={loading}
          >
            Гостевой вход (только просмотр)
          </Button>
        )}
      </div>
    </div>
  )
}

export default LoginPage
