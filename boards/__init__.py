# boards 패키지
# parser_name -> 파서 클래스를 연결하는 매핑 테이블

from boards.engineering import EngineeringParser
from boards.natural_sciences import NaturalSciencesParser

# config.json 의 parser_name 값과 클래스를 연결
PARSER_MAP = {
    "engineering": EngineeringParser,
    "natural_sciences": NaturalSciencesParser,
}
