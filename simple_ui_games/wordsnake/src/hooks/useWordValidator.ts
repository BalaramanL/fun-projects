
import { useEffect, useState } from 'react';
import { WordValidator } from '../services/WordValidator';

export function useWordValidator() {
  const [validator, setValidator] = useState<WordValidator | null>(null);

  useEffect(() => {
    const newValidator = new WordValidator();
    newValidator.loadDictionary().then(() => {
      setValidator(newValidator);
    });
  }, []);

  return validator;
}
