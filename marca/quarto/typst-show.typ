#show: doc => relatorio(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(date)$
  date: [$date$],
$endif$
$if(projeto)$
  projeto: [$projeto$],
$endif$
$if(fontes)$
  fontes: [$fontes$],
$endif$
  doc,
)
