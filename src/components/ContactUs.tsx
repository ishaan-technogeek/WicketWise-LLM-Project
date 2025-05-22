"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export const ContactUs = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>📞 Contact Us</CardTitle>
        <CardDescription>Get in touch with us for any queries or feedback.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>
          Email: <a href="mailto:support@wicketwise.com">support@wicketwise.com</a>
        </p>
        <p>Phone: +91 9182736455</p>
        <p>Address: T-12, Shankar Bhawan</p>
      </CardContent>
    </Card>
  );
};
