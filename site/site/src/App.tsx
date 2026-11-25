import { useEffect, useRef, useState } from 'react'
import ArrowDown from 'lucide-react/icons/arrow-down'
import ArrowRight from 'lucide-react/icons/arrow-right'
import ArrowUpRight from 'lucide-react/icons/arrow-up-right'
import BusFront from 'lucide-react/icons/bus-front'
import Camera from 'lucide-react/icons/camera'
import Check from 'lucide-react/icons/check'
import ChevronRight from 'lucide-react/icons/chevron-right'
import CircleHelp from 'lucide-react/icons/circle-help'
import LockKeyhole from 'lucide-react/icons/lock-keyhole'
import MapPin from 'lucide-react/icons/map-pin'
import MessageCircle from 'lucide-react/icons/message-circle'
import Phone from 'lucide-react/icons/phone'
import Printer from 'lucide-react/icons/printer'
import RefreshCcw from 'lucide-react/icons/refresh-ccw'
import ShieldCheck from 'lucide-react/icons/shield-check'
import Smartphone from 'lucide-react/icons/smartphone'
import type { LucideIcon } from 'lucide-react'
import { stepForProgress } from './story.ts'

const chapters = [
  {
    eyebrow: '01 / Start',
    title: 'Bare det familien trenger.',
    body: 'En gammel mobil kan få et nytt, enklere oppsett. Vi undersøker hvilke funksjoner som kan velges på akkurat deres modell.',
  },
  {
    eyebrow: '02 / Kontakt',
    title: 'Alltid en vei hjem.',
    body: 'Samtaler og SMS gjør det enkelt å gi beskjed når planen endrer seg. Hvilke kontakter som kan brukes, må avklares på den aktuelle mobilen.',
  },
  {
    eyebrow: '03 / Reisen',
    title: 'Bussen er en del av hverdagen.',
    body: 'Skyss kan være en av de utvalgte appene. Appen trenger nett for å kjøpe og vise billett, så vi må teste oppsettet på hver modell.',
  },
  {
    eyebrow: '04 / Utforskning',
    title: 'Plass til å finne veien.',
    body: 'Kart og kamera kan gi barnet praktisk frihet uten at hele appbutikken trenger å være åpen. De konkrete begrensningene varierer.',
  },
  {
    eyebrow: '05 / Foreldrene',
    title: 'Dere beholder oversikten.',
    body: 'Foreldrene får PIN-koden og en kort guide på ett ark: hva som er satt opp, hva som må følges opp, og hvor grensene går.',
  },
] as const

const apps: { label: string; Icon: LucideIcon; tone: string }[] = [
  { label: 'Ring', Icon: Phone, tone: 'mint' },
  { label: 'Melding', Icon: MessageCircle, tone: 'paper' },
  { label: 'Skyss', Icon: BusFront, tone: 'peach' },
  { label: 'Kart', Icon: MapPin, tone: 'paper' },
  { label: 'Kamera', Icon: Camera, tone: 'mint' },
]

function Brand({ light = false }: { light?: boolean }) {
  return (
    <a className={`brand ${light ? 'brand-light' : ''}`} href="#topp" aria-label="Safestart UB, til toppen">
      <img src="/safestart-symbol.svg" alt="" width="38" height="38" />
      <span>Safestart <small>UB</small></span>
    </a>
  )
}

function PhoneHome() {
  return (
    <div className="phone-content phone-home">
      <p className="phone-greeting">God morgen</p>
      <h3>Hei, Alex.</h3>
      <p className="phone-subtitle">Det viktigste er her.</p>
      <div className="phone-app-grid">
        {apps.map(({ label, Icon, tone }) => (
          <div className={`phone-app phone-app-${tone}`} key={label}>
            <Icon size={21} strokeWidth={2} />
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="phone-bottom-note"><ShieldCheck size={15} /> Et utvalg som familien bestemmer</div>
    </div>
  )
}

function PhoneCalls() {
  return (
    <div className="phone-content phone-calls">
      <span className="phone-mini-label">SAMTALER</span>
      <h3>Hjem er ett trykk unna.</h3>
      <div className="contact-card"><span className="contact-avatar">H</span><span><strong>Hjem</strong><small>Familiekontakt</small></span><Phone size={18} /></div>
      <div className="contact-card"><span className="contact-avatar contact-avatar-alt">F</span><span><strong>Foresatt</strong><small>Familiekontakt</small></span><MessageCircle size={18} /></div>
      <p className="phone-footnote">Eksempelvisning. Kontaktvalg avhenger av mobilen.</p>
    </div>
  )
}

function PhoneTransit() {
  return (
    <div className="phone-content phone-transit">
      <span className="phone-mini-label">PÅ FARTEN</span>
      <h3>En enklere vei til bussen.</h3>
      <div className="ticket-card">
        <div className="ticket-top"><BusFront size={24} /><span>Skyss</span></div>
        <strong>Reise og billett</strong>
        <p>Åpnes som utvalgt app</p>
        <div className="ticket-rule" />
        <small>Krever nettilgang og en støttet mobil</small>
      </div>
      <p className="phone-footnote">Konseptskisse, ikke en visning fra Skyss-appen.</p>
    </div>
  )
}

function PhoneExplore() {
  return (
    <div className="phone-content phone-explore">
      <span className="phone-mini-label">UTFORSK</span>
      <h3>Mer enn bare å ringe.</h3>
      <div className="explore-list">
        <div><span className="explore-icon"><MapPin size={24} /></span><span><strong>Kart</strong><small>Finn veien videre</small></span><ChevronRight size={16} /></div>
        <div><span className="explore-icon peach"><Camera size={24} /></span><span><strong>Kamera</strong><small>Ta vare på øyeblikk</small></span><ChevronRight size={16} /></div>
      </div>
      <div className="phone-bottom-note"><LockKeyhole size={15} /> Utvalgte funksjoner, modell for modell</div>
    </div>
  )
}

function PhoneGuide() {
  return (
    <div className="phone-content phone-guide">
      <span className="phone-mini-label">FAMILIENS OVERSIKT</span>
      <h3>Rammene blir tydelige.</h3>
      <div className="guide-preview">
        <div className="guide-preview-header"><img src="/safestart-symbol.svg" alt="" width="30" height="30" /><strong>Foreldreguide</strong></div>
        <div><Check size={16} /><span>Dette er satt opp</span></div>
        <div><Check size={16} /><span>Dette må dere følge opp</span></div>
        <div><Check size={16} /><span>PIN-koden blir hos dere</span></div>
      </div>
      <p className="phone-footnote">Guiden er under utvikling og testes sammen med oppsettet.</p>
    </div>
  )
}

function PhoneStory() {
  const sectionRef = useRef<HTMLElement>(null)
  const [step, setStep] = useState(0)

  useEffect(() => {
    let frame = 0
    const update = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const section = sectionRef.current
        if (!section) return
        const travel = Math.max(1, section.offsetHeight - window.innerHeight)
        const progress = -section.getBoundingClientRect().top / travel
        setStep(stepForProgress(progress, chapters.length))
      })
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [])

  const goToStep = (index: number) => {
    const section = sectionRef.current
    if (!section) return
    const top = window.scrollY + section.getBoundingClientRect().top
    const travel = Math.max(1, section.offsetHeight - window.innerHeight)
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.scrollTo({ top: top + travel * ((index + 0.12) / chapters.length), behavior: reduce ? 'auto' : 'smooth' })
    setStep(index)
  }

  return (
    <section className="story-track" id="opplev" ref={sectionRef} aria-labelledby="story-title">
      <div className="story-sticky">
        <div className="story-layout wrap">
          <div className="story-copy">
            <span className="eyebrow eyebrow-light"><span className="start-dot" /> SE KONSEPTET</span>
            <h2 id="story-title">En mobil som gir plass til det viktigste.</h2>
            <p className="story-intro">Rull videre. Her blar telefonen mens resten av fortellingen står i ro.</p>
            <div className="chapter-window" aria-live="off">
              {chapters.map((chapter, index) => (
                <div className={`chapter ${step === index ? 'is-active' : ''}`} key={chapter.eyebrow} aria-hidden={step !== index}>
                  <span>{chapter.eyebrow}</span>
                  <h3>{chapter.title}</h3>
                  <p>{chapter.body}</p>
                </div>
              ))}
            </div>
            <ol className="sr-only">
              {chapters.map((chapter) => <li key={chapter.eyebrow}>{chapter.title} {chapter.body}</li>)}
            </ol>
            <div className="chapter-controls" aria-label="Velg skjerm i telefonen">
              {chapters.map((chapter, index) => (
                <button
                  type="button"
                  key={chapter.eyebrow}
                  className={step === index ? 'is-active' : ''}
                  onClick={() => goToStep(index)}
                  aria-label={`Vis ${chapter.eyebrow.toLowerCase()}: ${chapter.title}`}
                  aria-current={step === index ? 'step' : undefined}
                ><span /></button>
              ))}
              <span className="chapter-count">0{step + 1} / 0{chapters.length}</span>
            </div>
          </div>
          <div className="story-visual">
            <div className="phone-halo" />
            <div className="phone-device" aria-hidden="true">
              <div className="phone-speaker" />
              <div className="phone-status"><span>08:15</span><span>•••  86%</span></div>
              <div className="phone-screen-stack">
                {[<PhoneHome />, <PhoneCalls />, <PhoneTransit />, <PhoneExplore />, <PhoneGuide />].map((screen, index) => (
                  <div className={`phone-screen ${step === index ? 'is-active' : ''}`} key={index}>{screen}</div>
                ))}
              </div>
              <div className="phone-homebar" />
            </div>
            <p className="phone-caption">Illustrasjon av mulig oppsett. Funksjoner og begrensninger må testes per mobil.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

const questions = [
  { q: 'Passer alle gamle mobiler?', a: 'Nei. Vi må sjekke om telefonen fortsatt får sikkerhetsoppdateringer, om de ønskede funksjonene virker, og hvilke begrensninger modellen støtter. En liste over testede modeller kommer først etter piloten.' },
  { q: 'Kan Skyss brukes uten internett?', a: 'Nei. Skyss opplyser at appen trenger nett for reisesøk, billettkjøp og visning av billett. Målet er å begrense unødvendig tilgang, ikke å koble telefonen helt fra nettet.' },
  { q: 'Er mobilen helt trygg etter oppsettet?', a: 'Ingen foreldrekontroll gir full beskyttelse. Vi vil vise hvilke innstillinger som er valgt, hva som er testet, og hva foreldrene fortsatt må følge opp.' },
  { q: 'Hva koster et oppsett eller en mobilkveld?', a: 'Prisen er ikke bestemt. Først må vi måle tidsbruk og kostnader og teste hva familier og FAU faktisk trenger.' },
  { q: 'Hva skjer med innholdet på den gamle mobilen?', a: 'Familien må ta vare på det den vil beholde før et eventuelt oppsett. Rutinen for sletting og kontroll må testes før tjenesten tilbys.' },
]

function App() {
  return (
    <>
      <header className="site-header" id="topp">
        <div className="wrap header-inner">
          <Brand />
          <nav aria-label="Hovedmeny" className="header-nav">
            <a href="#opplev">Se konseptet</a>
            <a href="#slik-fungerer-det">Slik fungerer det</a>
            <a href="#fau">For FAU</a>
            <a href="#sporsmal">Spørsmål</a>
          </nav>
          <a className="header-link" href="#opplev">Utforsk <ArrowUpRight size={17} /></a>
        </div>
      </header>

      <main className="overflow-x-clip">
        <section className="hero wrap" aria-labelledby="hero-title">
          <div className="hero-copy">
            <span className="eyebrow"><span className="start-dot" /> SAFESTART UB · BERGEN</span>
            <h1 id="hero-title">Første mobil.<br /><em>På deres premisser.</em></h1>
            <p>Vi vil gjøre mobilen dere allerede har klar for en enklere start: samtaler, SMS, kamera, kart og Skyss der modellen støtter det. Foreldrene får PIN-koden og en guide på ett ark.</p>
            <div className="hero-actions">
              <a className="button button-primary" href="#opplev">Se hvordan det kan fungere <ArrowRight size={18} /></a>
              <a className="text-link" href="#fau">For FAU og skoler <ArrowUpRight size={17} /></a>
            </div>
            <span className="hero-note"><CircleHelp size={17} /> Konsept under testing. Ingen pris eller modellstøtte er lovet ennå.</span>
          </div>
          <div className="hero-aside" aria-label="Slik er Safestart tenkt">
            <div className="hero-aside-head"><span>01 / 03</span><Smartphone size={24} /></div>
      <div className="hero-aside-main"><img src="/safestart-symbol.svg" width="85" height="85" alt="" /><h2>En god start med mobilen dere allerede har.</h2></div>
            <div className="hero-aside-steps"><span>Ta med mobilen</span><ChevronRight size={18} /><span>Vi setter den opp</span><ChevronRight size={18} /><span>Dere får oversikt</span></div>
          </div>
          <a className="scroll-hint" href="#hvorfor"><ArrowDown size={18} /> Rull for å utforske</a>
        </section>

        <section className="why-section" id="hvorfor" aria-labelledby="why-title">
          <div className="wrap why-grid">
            <div><span className="eyebrow"><span className="start-dot" /> HVA VI LØSER</span><h2 id="why-title">Kontakt uten at alt annet må følge med.</h2></div>
            <p>Noen familier vil at barnet skal kunne ringe hjem og reise med buss, men ønsker å vente med fri tilgang til nett og sosiale medier. Safestart undersøker hvordan familiens eksisterende mobil kan settes opp for det behovet.</p>
          </div>
          <div className="wrap feature-row" aria-label="Funksjoner i konseptet">
            {apps.map(({ label, Icon }) => <div className="feature" key={label}><Icon size={22} strokeWidth={1.9} /><span>{label}</span></div>)}
          </div>
        </section>

        <PhoneStory />

        <section className="process-section wrap" id="slik-fungerer-det" aria-labelledby="process-title">
          <div className="section-heading"><span className="eyebrow"><span className="start-dot" /> EN ENKEL PROSESS</span><h2 id="process-title">Fra skuff til første mobil.</h2><p>Dette er planen. Hvert trinn må prøves i en pilot før vi tilbyr tjenesten.</p></div>
          <div className="process-grid">
            <article><span className="process-number">01</span><RefreshCcw size={29} /><h3>Ta med mobilen</h3><p>Familien kommer med en mobil den allerede eier. Vi undersøker modell, oppdateringer og hva den kan brukes til.</p></article>
            <article><span className="process-number">02</span><Smartphone size={29} /><h3>Sett opp sammen</h3><p>Vi går gjennom sletting og ønskede funksjoner. Samtaler, SMS, kamera, kart og Skyss testes på den aktuelle mobilen.</p></article>
            <article><span className="process-number">03</span><LockKeyhole size={29} /><h3>Ta med oversikten hjem</h3><p>Foreldrene beholder PIN-koden og får en kort guide med innstillinger, begrensninger og det de må følge opp.</p></article>
          </div>
        </section>

        <section className="limits-section" aria-labelledby="limits-title">
          <div className="wrap limits-grid">
            <div><span className="eyebrow"><span className="start-dot" /> ÆRLIGE RAMMER</span><h2 id="limits-title">Trygghet begynner med å vite hva mobilen faktisk kan.</h2><p>Vi viser konkrete innstillinger og tester dem. Foreldrekontroll erstatter ikke samtalen mellom barn og voksne.</p><a className="text-link" href="#sporsmal">Les de vanlige spørsmålene <ArrowRight size={17} /></a></div>
            <div className="limits-card"><span className="limits-label">DET VI SJEKKER</span><ul><li><Check size={19} /> Får mobilen fortsatt oppdateringer?</li><li><Check size={19} /> Fungerer Skyss med nødvendig nett?</li><li><Check size={19} /> Holder de valgte begrensningene etter omstart?</li><li><Check size={19} /> Forstår familien hva oppsettet ikke løser?</li></ul></div>
          </div>
        </section>

        <section className="fau-section wrap" id="fau" aria-labelledby="fau-title">
          <div className="fau-panel">
            <div><span className="eyebrow eyebrow-light"><span className="start-dot" /> FOR FAU</span><h2 id="fau-title">En mobilkveld for hele trinnet?</h2><p>Flere familier kan ta med mobilen de allerede har. På én kveld kan vi gå gjennom mulige oppsett, spørsmål og en felles foreldreguide. Formatet er et forslag som må testes med FAU.</p><button className="button button-light" type="button" onClick={() => window.print()}><Printer size={18} /> Skriv ut oversikten</button></div>
            <div className="fau-agenda"><span>ET MULIG PROGRAM</span><ol><li><b>01</b><span>Ta med en mobil hjemmefra</span></li><li><b>02</b><span>Gå gjennom behov og oppsett</span></li><li><b>03</b><span>Ta med en kort guide hjem</span></li></ol></div>
          </div>
        </section>

        <section className="faq-section wrap" id="sporsmal" aria-labelledby="faq-title">
          <div className="section-heading"><span className="eyebrow"><span className="start-dot" /> SPØRSMÅL OG SVAR</span><h2 id="faq-title">Det foreldre bør vite.</h2></div>
          <div className="faq-list">{questions.map(({ q, a }) => <details key={q}><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>)}</div>
          <p className="source-note">Kilder for spørsmål om Skyss og foreldrekontroll: <a href="https://www.skyss.no/billett-og-pris/Kjop-av-billettar/appen-skyss/sp%C3%B8rsm%C3%A5l-og-svar-om-appen-skyss/" target="_blank" rel="noreferrer">Skyss</a> og <a href="https://www.medietilsynet.no/digitale-medier/skjermtid/foreldrekontroll/" target="_blank" rel="noreferrer">Medietilsynet</a>.</p>
        </section>

        <section className="end-section"><div className="wrap end-grid"><div><span className="eyebrow"><span className="start-dot" /> EN GOD START</span><h2>En mobil fra skuffen.<br />Et valg dere tar sammen.</h2></div><a className="button button-primary" href="#opplev">Se konseptet igjen <ArrowUpRight size={18} /></a></div></section>
      </main>

      <footer className="site-footer"><div className="wrap footer-grid"><Brand light /><p>Safestart UB · Amalie Skram vgs, Bergen<br />Konsept og visuell profil under testing.</p><a href="#topp">Til toppen ↑</a></div></footer>
    </>
  )
}

export default App
