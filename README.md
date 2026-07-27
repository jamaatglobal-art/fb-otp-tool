# Facebook Multi-Account OTP Tool (Upgraded)

এই টুলটি এখন `facebook-account-registration` রিপোজিটরির উন্নত টেকনোলজি ব্যবহার করে আপগ্রেড করা হয়েছে। এতে এখন **TLS Fingerprinting (curl_cffi)** এবং **Advanced User-Agent Rotation** যুক্ত করা হয়েছে যা ফেসবুকের ডিটেকশন এড়াতে সাহায্য করবে।

## নতুন ফিচারসমূহ:
- **TLS Fingerprinting**: ব্রাউজারের আসল ফিঙ্গারপ্রিন্ট নকল করে (curl_cffi ব্যবহার করে)।
- **Advanced User-Agents**: বাস্তবসম্মত মোবাইল এবং অ্যাপ ইউজার-এজেন্ট জেনারেশন।
- **Better Session Management**: উন্নত সেশন এবং কুকি হ্যান্ডলিং।
- **Clean UI**: নতুন কালারফুল ইন্টারফেস এবং কাউন্টার।

## কিভাবে ব্যবহার করবেন:
১. প্রয়োজনীয় লাইব্রেরি ইনস্টল করুন:
   ```bash
   pip install curl_cffi faker requests
   ```
২. `accounts.json` ফাইলে আপনার ফেসবুক একাউন্টের তথ্য এবং কুকিজ দিন।
৩. টুলটি রান করুন:
   ```bash
   python fb_automation.py
   ```

## একাউন্ট কনফিগারেশন (`accounts.json`):
```json
{
    "account1": {
        "identifier": "example@email.com",
        "cookies": {
            "c_user": "xxxx",
            "xs": "xxxx",
            "datr": "xxxx",
            "fr": "xxxx"
        }
    }
}
```
