import * as React from 'react'
import { useContext, useEffect, useRef, useState } from 'react'
import { ITextField, Stack, Checkbox } from '@fluentui/react'
import { UploadedDocument } from '../../api/models'
import { AppStateContext } from '../../state/AppProvider'

import styles from './DocumentListPanel.module.css'

interface Props {
  item: UploadedDocument,
  isSelected: boolean,
  onSelect: (id: string, checked:boolean) => void  
}

export const DocumentListItem: React.FC<Props> = ({ item, isSelected, onSelect }) => {
    const [textFieldFocused, setTextFieldFocused] = useState(false)
    const textFieldRef = useRef<ITextField | null>(null)
    const appStateContext = useContext(AppStateContext)

    useEffect(() => {
      if (textFieldFocused && textFieldRef.current) {
        textFieldRef.current.focus()
        setTextFieldFocused(false)
      }
    }, [textFieldFocused])
  
    return (
      <Stack
        key={item.id.toString()}
        tabIndex={0}
        aria-label="uploaded document item"
        className={styles.itemCell}
        verticalAlign="center"
        onClick={() => onSelect(item.id.toString(), !isSelected)}
        styles={{
          root: {
            backgroundColor: isSelected ? '#e6e6e6' : 'transparent'
          }
        }}>
            <Stack horizontal verticalAlign={'center'} style={{ width: '100%' }}>
                <Checkbox checked={isSelected} onChange={(e, checked) => onSelect(item.id.toString(), checked || false)} />
                <span>{item.id}</span>
            </Stack>
      </Stack>
    )
  }