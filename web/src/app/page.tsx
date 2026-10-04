import Navbar from '@/components/Navbar';
import HeroSection from '@/components/HeroSection';
import FeaturesSection from '@/components/FeaturesSection';
import ArchitectureSection from '@/components/ArchitectureSection';
import CapabilitiesSection from '@/components/CapabilitiesSection';
import APISection from '@/components/APISection';
import DemoSection from '@/components/DemoSection';
import Footer from '@/components/Footer';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <ArchitectureSection />
        <CapabilitiesSection />
        <APISection />
        <DemoSection />
      </main>
      <Footer />
    </>
  );
}
