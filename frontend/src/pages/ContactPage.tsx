import { Card, CardContent } from "../components/common/Card";
import { TextInput } from "../components/common/TextInput";
import { TextArea } from "../components/common/TextArea";
import { Button } from "../components/common/Button";

export default function ContactPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold mb-4 text-center">Contact Us</h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8 text-center max-w-lg mx-auto">Have questions about AIATS, need support, or want to give feedback? We'd love to hear from you.</p>
      
      <Card>
        <CardContent className="p-8">
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            <div className="grid sm:grid-cols-2 gap-6">
              <TextInput label="First Name" placeholder="Jane" />
              <TextInput label="Last Name" placeholder="Doe" />
            </div>
            <TextInput label="Email Address" type="email" placeholder="jane@example.com" />
            <TextArea label="Message" placeholder="How can we help?" className="min-h-[120px]" />
            <Button size="lg" className="w-full">Send Message</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
