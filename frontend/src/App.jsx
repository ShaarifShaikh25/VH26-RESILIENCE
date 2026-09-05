import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import NetworkSection from './components/NetworkSection'
import Footer from './components/Footer'

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <NetworkSection />
      </main>
      <Footer />
    </>
  )
}
