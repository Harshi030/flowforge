from abc import ABC, abstractmethod

class EmailProvider(ABC):
  @abstractmethod
  def send(
    self,
    to: str,
    subject: str,
    html: str,
  ) -> None:
    pass
  
class ConsoleEmailProvider(EmailProvider):
  def send(self, to, subject, html):
    print("----- EMAIL -----")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(html)
    print("-----------------")