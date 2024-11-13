import React, { ReactNode } from 'react';

import styles from './Card.module.css'

interface Props {
  children: ReactNode;
}

export const Card: React.FC<Props> = ({ children }) => {
  return (
    <div className={styles.card}>
      <div className={styles.cardBody}>
        {children}
      </div>
    </div>
  );
}
