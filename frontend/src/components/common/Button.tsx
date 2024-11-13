import { CommandBarButton, DefaultButton, IButtonProps } from '@fluentui/react'

import styles from './Button.module.css'

interface ButtonProps extends IButtonProps {
  onClick: () => void
  text: string | undefined
}

interface HeaderButtonProps extends ButtonProps {
  iconName: string
}

export const ShareButton: React.FC<ButtonProps> = ({ onClick, text }) => {
  return (
    <CommandBarButton
      className={styles.shareButtonRoot}
      iconProps={{ iconName: 'Share' }}
      onClick={onClick}
      text={text}
    />
  )
}

export const HeaderButton: React.FC<HeaderButtonProps> = ({ iconName, onClick, text }) => {
  return (
    <DefaultButton
      className={styles.headerButtonRoot}
      text={text}
      iconProps={{ iconName: iconName }}
      onClick={onClick}
    />
  )
}
