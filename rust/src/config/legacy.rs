use serde_json::{Map, Number, Value};

use crate::error::{Error, Result};

pub fn parse(input: &str) -> Result<Value> {
    let mut parser = Parser {
        characters: input.chars().collect(),
        position: 0,
    };
    let value = parser.value()?;
    parser.whitespace();
    if parser.position != parser.characters.len() {
        return Err(parser.error("unexpected trailing content"));
    }
    Ok(value)
}

struct Parser {
    characters: Vec<char>,
    position: usize,
}

impl Parser {
    fn value(&mut self) -> Result<Value> {
        self.whitespace();
        match self.peek() {
            Some('{') => self.object(),
            Some('[') => self.array(']'),
            Some('(') => self.array(')'),
            Some('"') | Some('\'') => self.string().map(Value::String),
            Some('T') => self.keyword("True", Value::Bool(true)),
            Some('F') => self.keyword("False", Value::Bool(false)),
            Some('N') => self.keyword("None", Value::Null),
            Some('-' | '0'..='9') => self.number(),
            Some(character) => Err(self.error(&format!("unexpected character `{character}`"))),
            None => Err(self.error("expected a value")),
        }
    }

    fn object(&mut self) -> Result<Value> {
        self.consume('{')?;
        let mut map = Map::new();
        self.whitespace();
        if self.take_if('}') {
            return Ok(Value::Object(map));
        }
        loop {
            self.whitespace();
            let key = self.string()?;
            self.whitespace();
            self.consume(':')?;
            let value = self.value()?;
            map.insert(key, value);
            self.whitespace();
            if self.take_if('}') {
                break;
            }
            self.consume(',')?;
            self.whitespace();
            if self.take_if('}') {
                break;
            }
        }
        Ok(Value::Object(map))
    }

    fn array(&mut self, terminator: char) -> Result<Value> {
        self.position += 1;
        let mut values = Vec::new();
        self.whitespace();
        if self.take_if(terminator) {
            return Ok(Value::Array(values));
        }
        loop {
            values.push(self.value()?);
            self.whitespace();
            if self.take_if(terminator) {
                break;
            }
            self.consume(',')?;
            self.whitespace();
            if self.take_if(terminator) {
                break;
            }
        }
        Ok(Value::Array(values))
    }

    fn string(&mut self) -> Result<String> {
        let quote = self
            .peek()
            .filter(|quote| matches!(quote, '"' | '\''))
            .ok_or_else(|| self.error("object keys and strings must be quoted"))?;
        self.position += 1;
        let mut result = String::new();
        loop {
            let character = self
                .next()
                .ok_or_else(|| self.error("unterminated string"))?;
            if character == quote {
                return Ok(result);
            }
            if character != '\\' {
                result.push(character);
                continue;
            }
            let escaped = self
                .next()
                .ok_or_else(|| self.error("unterminated escape"))?;
            match escaped {
                '\\' | '\'' | '"' | '/' => result.push(escaped),
                'b' => result.push('\u{0008}'),
                'f' => result.push('\u{000c}'),
                'n' => result.push('\n'),
                'r' => result.push('\r'),
                't' => result.push('\t'),
                'u' => {
                    let mut digits = String::new();
                    for _ in 0..4 {
                        digits.push(
                            self.next()
                                .ok_or_else(|| self.error("incomplete unicode escape"))?,
                        );
                    }
                    let code = u32::from_str_radix(&digits, 16)
                        .map_err(|_| self.error("invalid unicode escape"))?;
                    let decoded =
                        char::from_u32(code).ok_or_else(|| self.error("invalid unicode scalar"))?;
                    result.push(decoded);
                }
                other => {
                    result.push('\\');
                    result.push(other);
                }
            }
        }
    }

    fn number(&mut self) -> Result<Value> {
        let start = self.position;
        while matches!(self.peek(), Some('-' | '+' | '.' | '0'..='9' | 'e' | 'E')) {
            self.position += 1;
        }
        let text = self.characters[start..self.position]
            .iter()
            .collect::<String>();
        let number = text
            .parse::<Number>()
            .map_err(|_| self.error("invalid number"))?;
        Ok(Value::Number(number))
    }

    fn keyword(&mut self, keyword: &str, value: Value) -> Result<Value> {
        let end = self.position + keyword.chars().count();
        if self.characters.get(self.position..end)
            == Some(keyword.chars().collect::<Vec<_>>().as_slice())
        {
            self.position = end;
            Ok(value)
        } else {
            Err(self.error(&format!("expected `{keyword}`")))
        }
    }

    fn whitespace(&mut self) {
        while self.peek().is_some_and(char::is_whitespace) {
            self.position += 1;
        }
    }

    fn consume(&mut self, expected: char) -> Result<()> {
        if self.take_if(expected) {
            Ok(())
        } else {
            Err(self.error(&format!("expected `{expected}`")))
        }
    }

    fn take_if(&mut self, expected: char) -> bool {
        if self.peek() == Some(expected) {
            self.position += 1;
            true
        } else {
            false
        }
    }

    fn peek(&self) -> Option<char> {
        self.characters.get(self.position).copied()
    }

    fn next(&mut self) -> Option<char> {
        let value = self.peek();
        if value.is_some() {
            self.position += 1;
        }
        value
    }

    fn error(&self, message: &str) -> Error {
        Error::Config(format!(
            "legacy configuration parse error at character {}: {message}",
            self.position
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::parse;

    #[test]
    fn parses_python_literals_and_trailing_commas() {
        let value =
            parse("{'dns': 'alidns', 'enabled': True, 'none': None, 'items': (1, 2,),}").unwrap();
        assert_eq!(
            value,
            serde_json::json!({
                "dns": "alidns",
                "enabled": true,
                "none": null,
                "items": [1, 2]
            })
        );
    }

    #[test]
    fn rejects_executable_expressions() {
        assert!(parse("{'token': open('secret')}").is_err());
    }
}
